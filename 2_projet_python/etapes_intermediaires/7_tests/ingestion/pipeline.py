"""la pipeline ne manipule plus que des abstractions (BaseConnector, DatasetWriter) pas de if/elif

writer et fabrique de connecteurs sont injectés : en test on lui donne des faux objets, pas besoin de base ni de bucket
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from ingestion.config import SourceConfig, TableConfig
from ingestion.connectors import BaseConnector, create_connector
from ingestion.transform import normalize
from ingestion.writers import DatasetWriter


@dataclass
class TableResult:
    source: str
    table: str
    rows: int
    uri: str


class IngestionPipeline:
    def __init__(
        self,
        writer: DatasetWriter,
        load_date: str,
        connector_factory: Callable[[SourceConfig], BaseConnector] = create_connector,
    ) -> None:
        self.writer = writer
        self.load_date = load_date
        self.connector_factory = connector_factory

    def run(self, sources: list[SourceConfig]) -> list[TableResult]:
        results: list[TableResult] = []
        for source in sources:
            with self.connector_factory(source) as connector:
                for table in source.tables:
                    results.append(self.ingest_table(connector, source, table))
        return results

    def ingest_table(self, connector: BaseConnector, source: SourceConfig, table: TableConfig) -> TableResult:
        df = normalize(connector.extract(table))
        uri = self.writer.write(df, source.name, table.target, self.load_date)
        return TableResult(source=source.name, table=table.target, rows=len(df), uri=uri)
