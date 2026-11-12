"""Fixtures + fakes partagés par tous les tests
une fixture c est une ressource préparée par pytest, et injectée par son nom dans
les tests qui la demandent en paramètre
les fakes remplacent les vraies bases et le vrai bucket
"""
from __future__ import annotations

import duckdb
import pandas as pd
import pytest

from ingestion.config import SourceConfig, TableConfig
from ingestion.connectors import BaseConnector
from ingestion.writers import Storage


class InMemoryStorage(Storage):
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    def put(self, key: str, body: bytes) -> str:
        self.objects[key] = body
        return f"memory://{key}"


class FakeConnector(BaseConnector):
    def __init__(self, source: SourceConfig, data: dict[str, pd.DataFrame]) -> None:
        super().__init__(source)
        self.data = data
        self.opened = 0
        self.closed = 0

    def _open(self) -> None:
        self.opened += 1

    def _read(self, query: str) -> pd.DataFrame:
        table = query.split()[-1]                    # hack : "SELECT * FROM xxx" -> "xxx", suffit pr les tests
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
def duckdb_file(tmp_path):
    # une vraie base duckdb, dans tmp_path donc pytest fait le ménage après
    path = tmp_path / "test.duckdb"
    with duckdb.connect(str(path)) as con:
        con.execute("CREATE TABLE produits (CodeUCD VARCHAR, Libelle VARCHAR)")
        con.execute("INSERT INTO produits VALUES ('001', ' Paracétamol '), ('002', 'Ibuprofène')")
    return path
