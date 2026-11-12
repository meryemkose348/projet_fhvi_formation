"""Pipeline : extraction -> normalisation -> métadonnées -> écriture, table par table

Une table qui plante est loggée et comptée, les autres continuent
"""
from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime

from fhvi_ingestion.config import SourceConfig, TableConfig
from fhvi_ingestion.connectors import BaseConnector, create_connector
from fhvi_ingestion.metadata import add_technical_columns
from fhvi_ingestion.report import RunReport, Status, TableResult
from fhvi_ingestion.run_context import RunContext
from fhvi_ingestion.transform import normalize
from fhvi_ingestion.writers import DatasetWriter

logger = logging.getLogger(__name__)


class PipelineAborted(RuntimeError):
    def __init__(self, message: str, report: RunReport | None = None) -> None:
        super().__init__(message)
        self.report = report


class IngestionPipeline:
    def __init__(
        self,
        writer: DatasetWriter,
        run: RunContext,
        connector_factory: Callable[[SourceConfig], BaseConnector] = create_connector,
        fail_fast: bool = False,
    ) -> None:
        self.writer = writer
        self.run_context = run
        self.connector_factory = connector_factory
        self.fail_fast = fail_fast

    def run(self, sources: list[SourceConfig]) -> RunReport:
        report = RunReport(run=self.run_context)
        logger.info("Début du run - date de chargement %s - %d source(s) : %s",
                    self.run_context.load_date, len(sources), ", ".join(s.name for s in sources))
        if self.run_context.replay_of:
            logger.info("Rejeu du run %s", self.run_context.replay_of)
        try:
            for source in sources:
                self._run_source(source, report)
        except PipelineAborted as exc:
            done = {(r.source, r.table) for r in report.results}
            for source in sources:
                for table in source.tables:
                    if (source.name, table.target) not in done:
                        report.add(TableResult(source.name, table.target, Status.FAILED,
                                               error="non lancée (arrêt --fail-fast)"))
            exc.report = report
            raise
        finally:
            report.finish()
            self._log_summary(report)
        return report

    def _run_source(self, source: SourceConfig, report: RunReport) -> None:
        logger.info("[%s] Connexion (%s) - %d table(s)", source.name, source.type, len(source.tables))
        try:
            connector = self.connector_factory(source)
            connector.open()
        except Exception as exc:
            self._handle_error(source, None, exc)
            for table in source.tables:
                report.add(TableResult(source.name, table.target, Status.FAILED, error=_describe(exc)))
            self._abort_if_fail_fast(source.name, _describe(exc))
            return
        try:
            for table in source.tables:
                result = self._ingest_table(connector, source, table)
                report.add(result)
                if result.status is Status.FAILED:
                    self._abort_if_fail_fast(f"{source.name}.{table.name}", result.error)
        finally:
            connector.close()
            logger.debug("[%s] Connexion fermée", source.name)

    def _ingest_table(self, connector: BaseConnector, source: SourceConfig, table: TableConfig) -> TableResult:
        start = time.perf_counter()
        try:
            extracted_at = datetime.now(UTC)
            # {load_date} remplacé par la date du run : rejouer une date relit les mêmes lignes
            df = connector.extract(replace(table, query=table.sql_for(self.run_context.load_date)))
            logger.debug("[%s.%s] %d lignes lues, colonnes source : %s",
                         source.name, table.name, len(df), list(df.columns))
            if df.empty:
                logger.warning("[%s.%s] La table est vide", source.name, table.name)

            df = normalize(df)
            df = add_technical_columns(df, self.run_context, source.name, table.name,
                                       extracted_at=extracted_at, load_timestamp=datetime.now(UTC))
            uri = self.writer.write(df, source.name, table.target, self.run_context)

            duration = round(time.perf_counter() - start, 3)
            logger.info("[%s.%s] OK - %d lignes en %.2f s -> %s", source.name, table.name, len(df), duration, uri)
            return TableResult(source.name, table.target, Status.SUCCESS, rows=len(df), uri=uri, duration_s=duration)
        except Exception as exc:
            self._handle_error(source, table, exc)
            return TableResult(source.name, table.target, Status.FAILED,
                               duration_s=round(time.perf_counter() - start, 3), error=_describe(exc))

    @staticmethod
    def _handle_error(source: SourceConfig, table: TableConfig | None, exc: Exception) -> None:
        where = f"{source.name}.{table.name}" if table else source.name
        # traceback seulement en DEBUG, sinon une ligne lisible suffit dnas les logs
        logger.error("[%s] ÉCHEC - %s", where, _describe(exc), exc_info=logger.isEnabledFor(logging.DEBUG))

    def _abort_if_fail_fast(self, where: str, error: str | None) -> None:
        if self.fail_fast:
            logger.critical("Arrêt immédiat du run (--fail-fast) après l'échec de %s", where)
            raise PipelineAborted(f"échec de {where} : {error}")

    @staticmethod
    def _log_summary(report: RunReport) -> None:
        level = logging.INFO if report.status is Status.SUCCESS else logging.WARNING
        logger.log(level, "Fin du run - statut %s - %d/%d table(s) OK - %d lignes - %.2f s",
                   report.status.value, len(report.results) - len(report.failed), len(report.results),
                   sum(r.rows for r in report.results), report.duration_s)
        for failed in report.failed:
            logger.log(level, "  table en échec : %s.%s -> %s", failed.source, failed.table, failed.error)


# les erreurs sql font facilement 30 lignes : on garde type + 1re ligne
def _describe(exc: Exception) -> str:
    first_line = str(exc).strip().splitlines()[0] if str(exc).strip() else ""
    return f"{type(exc).__name__}: {first_line}"[:300]
