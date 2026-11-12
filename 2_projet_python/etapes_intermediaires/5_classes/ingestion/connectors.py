"""def des connecteurs où on a un objet par source, qui garde sa connexion ouverte

À l'étape 4 chaque extract() recréait un moteur SQLAlchemy, donc 2 tables = 2 connexions
Un connecteur a un état (la connexion) et des comportements (lire, fermer) : c est le cas d'une classe
"""
from __future__ import annotations

import duckdb
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from ingestion.config import SourceConfig, TableConfig


class PostgresConnector:
    def __init__(self, source: SourceConfig) -> None:
        self.source = source
        c = source.connection
        url = f"postgresql+psycopg://{c['user']}:{c['password']}@{c['host']}:{c['port']}/{c['database']}"
        self._engine: Engine = create_engine(url)

    def read(self, table: TableConfig) -> pd.DataFrame:
        return pd.read_sql(table.sql, self._engine)

    def close(self) -> None:
        self._engine.dispose()


class MariaDBConnector:
    # presque meme chose que le PostgresConnector, seul le driver change. on factorise à l'étape 6

    def __init__(self, source: SourceConfig) -> None:
        self.source = source
        c = source.connection
        url = f"mysql+pymysql://{c['user']}:{c['password']}@{c['host']}:{c['port']}/{c['database']}"
        self._engine: Engine = create_engine(url)

    def read(self, table: TableConfig) -> pd.DataFrame:
        return pd.read_sql(table.sql, self._engine)

    def close(self) -> None:
        self._engine.dispose()


class SqlServerConnector:
    # presque idem que le connecteur précédent

    def __init__(self, source: SourceConfig) -> None:
        self.source = source
        c = source.connection
        url = f"mssql+pymssql://{c['user']}:{c['password']}@{c['host']}:{c['port']}/{c['database']}"
        self._engine: Engine = create_engine(url)

    def read(self, table: TableConfig) -> pd.DataFrame:
        return pd.read_sql(table.sql, self._engine)

    def close(self) -> None:
        self._engine.dispose()


class DuckDBConnector:
    def __init__(self, source: SourceConfig) -> None:
        self.source = source
        self._con = duckdb.connect(source.connection["path"], read_only=True)

    def read(self, table: TableConfig) -> pd.DataFrame:
        return self._con.execute(table.sql).df()

    def close(self) -> None:
        self._con.close()


def build_connector(source: SourceConfig):
    # trop de if/elif : besoin d'un register factory qui sera mis en place dans l etape juste apres
    if source.type == "postgres":
        return PostgresConnector(source)
    if source.type == "mariadb":
        return MariaDBConnector(source)
    if source.type == "sqlserver":
        return SqlServerConnector(source)
    if source.type == "duckdb":
        return DuckDBConnector(source)
    raise ValueError(f"Type de source non géré : {source.type}")
