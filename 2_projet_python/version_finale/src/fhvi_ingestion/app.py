"""ici on choisit les composants concrets et on les branche
"""
from __future__ import annotations

import logging
import sys
from dataclasses import replace

from fhvi_ingestion.cli import parse_args
from fhvi_ingestion.config import ConfigError, load_config
from fhvi_ingestion.connectors import available_connectors
from fhvi_ingestion.logging_setup import configure_logging
from fhvi_ingestion.pipeline import IngestionPipeline, PipelineAborted
from fhvi_ingestion.report import RunReport
from fhvi_ingestion.run_context import RunContext
from fhvi_ingestion.writers import FORMATS, DatasetWriter, available_storages, build_storage, get_format

logger = logging.getLogger("fhvi_ingestion")

# ce que l'ordonnanceur voit : 0 ok, 1 au moins une table KO, 2 : config/sélection invalide
EXIT_OK, EXIT_TABLE_FAILURE, EXIT_CONFIG_ERROR = 0, 1, 2


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    # run créé avant tout le reste pour que même l'erreur de config ait son run_id dans les logs
    run = RunContext.create(load_date=args.load_date)
    configure_logging(args.log_level, run_id=run.run_id, log_file=args.log_file)

    try:
        config = load_config(args.config, available_connectors(), available_storages(), FORMATS)
    except ConfigError as exc:
        logger.critical("Configuration invalide : %s", exc)
        return EXIT_CONFIG_ERROR

    if args.list_sources:
        for s in config.sources:
            state = "activée " if s.enabled else "désactivée"
            print(f"{s.name:<12} {s.type:<9} {state}  tables={[t.name for t in s.tables]}")
        return EXIT_OK

    destination = config.destination
    writer = DatasetWriter(
        storage=build_storage(destination, dry_run=args.dry_run),
        file_format=get_format(destination.format),
        prefix=destination.prefix,
        write_mode=destination.write_mode,
    )

    try:
        if args.rerun_failed:
            manifest = writer.read_report(args.rerun_failed)
            failed = [f"{r['source']}.{r['table']}" for r in manifest["results"] if r["status"] == "FAILED"]
            if not failed:
                logger.info("Run %s : aucune table en échec, rien à rejouer", args.rerun_failed)
                return EXIT_OK
            # on reprend la load_date du run d'origine, pas celle de la CLI (qui vaut aujourd'hui par défaut)
            run = replace(run, load_date=manifest["load_date"], replay_of=args.rerun_failed)
            logger.info("Rejeu des %d table(s) en échec du run %s (date de chargement %s) : %s",
                        len(failed), args.rerun_failed, run.load_date, ", ".join(failed))
            sources = config.select_tables(failed)
        elif args.tables:
            sources = config.select_tables(args.tables)
        else:
            sources = config.select(args.sources)
    except FileNotFoundError as exc:
        logger.critical("Rejeu impossible : %s", exc)
        return EXIT_CONFIG_ERROR
    except ConfigError as exc:
        logger.critical("Sélection invalide : %s", exc)
        return EXIT_CONFIG_ERROR

    pipeline = IngestionPipeline(writer, run, fail_fast=args.fail_fast)
    if args.dry_run:
        logger.warning("Mode --dry-run : aucune donnée ne sera écrite")

    try:
        report = pipeline.run(sources)
    except PipelineAborted as exc:
        # même en --fail-fast on écrit le manifeste
        if exc.report is not None:
            _write_manifest(writer, exc.report)
        return EXIT_TABLE_FAILURE

    _write_manifest(writer, report)
    return report.exit_code


# manifeste rangé à côté des données, c est lui que relit --rerun-failed
def _write_manifest(writer: DatasetWriter, report: RunReport) -> None:
    try:
        logger.info("Manifeste du run : %s", writer.write_report(report))
    except Exception as exc:  # noqa: BLE001 car le manifeste ne doit pas masquer le statut du run
        logger.error("Impossible d'écrire le manifeste du run : %s", exc)


def run() -> None:
    sys.exit(main())


if __name__ == "__main__":
    run()
