"""Contrat commun des connecteurs

Template Method : extract() fixe l'ordre (ouvrir si besoin, lire, vérifier le résultat), les
sous-classes ne codent que les étapes variables _open / _read / _close. Impossible d'en oublier une.
Chaque sous-classe joue aussi l'Adapter : elle branche une API (SQLAlchemy, DuckDB...) sur cette
interface, et le pipeline ne voit que extract(table) et close()
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

import pandas as pd

from ingestion.config import SourceConfig, TableConfig


class BaseConnector(ABC):
    type_name: ClassVar[str] = ""
    required_keys: ClassVar[tuple[str, ...]] = ()

    def __init__(self, source: SourceConfig) -> None:
        self.source = source
        self._is_open = False

    # la template method, à ne pas surcharger dans les sous-classes
    def extract(self, table: TableConfig) -> pd.DataFrame:
        if not self._is_open:
            self.open()
        df = self._read(table.sql)
        if not isinstance(df, pd.DataFrame):
            raise TypeError(f"{type(self).__name__}._read() doit retourner un DataFrame")
        return df

    def open(self) -> None:
        self._open()
        self._is_open = True

    def close(self) -> None:
        if self._is_open:
            self._close()
            self._is_open = False

    def __enter__(self) -> BaseConnector:
        self.open()
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()

    @abstractmethod
    def _open(self) -> None:
        """ouvre la connexion"""

    @abstractmethod
    def _read(self, query: str) -> pd.DataFrame:
        """exécute la requête, renvoie un DataFrame"""

    @abstractmethod
    def _close(self) -> None:
        """libère la connexion"""
