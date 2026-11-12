from __future__ import annotations

from datetime import UTC, datetime

import duckdb
import pandas as pd
import pytest

from fhvi_ingestion.config import SourceConfig, TableConfig
from fhvi_ingestion.connectors import BaseConnector
from fhvi_ingestion.run_context import RunContext
from fhvi_ingestion.writers import Storage


class InMemoryStorage(Storage):
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    def put(self, key: str, body: bytes) -> str:
        self.objects[key] = body
        return f"memory://{key}"

    def list_keys(self, prefix: str) -> list[str]:
        return sorted(k for k in self.objects if k.startswith(prefix))

    def get(self, key: str) -> bytes:
        if key not in self.objects:
            raise FileNotFoundError(key)
        return self.objects[key]

    def delete(self, key: str) -> None:
        self.objects.pop(key, None)


class FakeConnector(BaseConnector):
    def __init__(self, source: SourceConfig, data: dict[str, pd.DataFrame]) -> None:
        super().__init__(source)
        self.data = data
        self.opened = 0
        self.closed = 0

    def _open(self) -> None:
        self.opened += 1

    def _read(self, query: str) -> pd.DataFrame:
        table = query.split()[-1]
        if table not in self.data:
            raise RuntimeError(f"table {table} indisponible")
        return self.data[table].copy()

    def _close(self) -> None:
        self.closed += 1


@pytest.fixture
def raw_df() -> pd.DataFrame:
    return pd.DataFrame({
        "ID_RDV": [1, 2, 3],
        "Specialite": [" Cardiologie", "Pédiatrie ", "ophtalmologie"],
        "DateRdv": pd.to_datetime(["2026-01-05", "2026-01-06", "2026-01-07"]),
    })


@pytest.fixture
def make_source():
    def _make(name: str = "src_test", type_: str = "fake", tables: list[str] | None = None,
              connection: dict | None = None) -> SourceConfig:
        tables = tables or ["patients"]
        return SourceConfig(
            name=name, type=type_, connection=connection or {},
            tables=[TableConfig(name=t, target=t.lower()) for t in tables],
        )
    return _make


@pytest.fixture
def memory_storage() -> InMemoryStorage:
    return InMemoryStorage()


@pytest.fixture
def run_context() -> RunContext:
    return RunContext(
        run_id="20261109T020000Z-abcd1234",
        load_date="2026-11-09",
        started_at=datetime(2026, 11, 9, 2, 0, 0, tzinfo=UTC),
    )


@pytest.fixture
def duckdb_file(tmp_path):
    path = tmp_path / "test.duckdb"
    with duckdb.connect(str(path)) as con:
        con.execute("CREATE TABLE produits (CodeUCD VARCHAR, Libelle VARCHAR)")
        con.execute("INSERT INTO produits VALUES ('001', ' Paracétamol '), ('002', 'Ibuprofène')")
    return path
