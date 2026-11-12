"""Adapter DuckDB : pas d'engine ni de pd.read_sql ici, c'est connect / execute / df"""
from __future__ import annotations

import duckdb
import pandas as pd

from fhvi_ingestion.connectors.base import BaseConnector
from fhvi_ingestion.connectors.factory import register_connector


@register_connector("duckdb")
class DuckDBConnector(BaseConnector):
    required_keys = ("path",)

    def _open(self) -> None:
        self._con = duckdb.connect(self.source.connection["path"], read_only=True)

    def _read(self, query: str) -> pd.DataFrame:
        return self._con.execute(query).df()

    def _close(self) -> None:
        self._con.close()
