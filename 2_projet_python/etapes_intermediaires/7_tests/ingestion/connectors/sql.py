"""connecteurs SQL via SQLAlchemy : on factorise par héritage
"""
from __future__ import annotations

from typing import ClassVar

import pandas as pd
from sqlalchemy import URL, create_engine, text
from sqlalchemy.engine import Engine

from ingestion.connectors.base import BaseConnector
from ingestion.connectors.factory import register_connector


class SqlAlchemyConnector(BaseConnector):
    driver: ClassVar[str] = ""
    required_keys = ("host", "port", "database", "user", "password")

    def _build_url(self) -> URL:
        c = self.source.connection
        return URL.create(self.driver, username=c["user"], password=c["password"],
                          host=c["host"], port=int(c["port"]), database=c["database"])

    def _open(self) -> None:
        self._engine: Engine = create_engine(self._build_url(), pool_pre_ping=True)

    def _read(self, query: str) -> pd.DataFrame:
        with self._engine.connect() as con:
            return pd.read_sql(text(query), con)

    def _close(self) -> None:
        self._engine.dispose()


@register_connector("postgres")
class PostgresConnector(SqlAlchemyConnector):
    driver = "postgresql+psycopg"


@register_connector("mariadb")
class MariaDBConnector(SqlAlchemyConnector):
    driver = "mysql+pymysql"


@register_connector("sqlserver")
class SqlServerConnector(SqlAlchemyConnector):
    driver = "mssql+pymssql"
