"""pour chaque table la pipeline fait : connecteur -> normalize -> writer"""
from __future__ import annotations

from dataclasses import dataclass

from ingestion.config import PipelineConfig, SourceConfig
from ingestion.connectors import build_connector
from ingestion.transform import normalize
from ingestion.writer import DatasetWriter


@dataclass
class TableResult:
    source: str
    table: str
    rows: int
    uri: str


class IngestionPipeline:
    def __init__(self, config: PipelineConfig, load_date: str, dry_run: bool = False) -> None:
        self.config = config
        self.load_date = load_date
        self.dry_run = dry_run
        self.writer = DatasetWriter(config.destination)

    def run(self, sources: list[SourceConfig]) -> list[TableResult]:
        results: list[TableResult] = []
        for source in sources:
            connector = build_connector(source)
            try:
                for table in source.tables:
                    results.append(self._ingest_table(connector, source, table))
            finally:
                connector.close()
        return results

    def _ingest_table(self, connector, source, table) -> TableResult:
        df = normalize(connector.read(table))
        uri = "(dry-run)" if self.dry_run else self.writer.write(df, source.name, table.target, self.load_date)
        return TableResult(source=source.name, table=table.target, rows=len(df), uri=uri)
