"""connecteurs SQLAlchemy : postgres, mariaDB et sql server partagent tout sauf le driver -> héritage"""
from __future__ import annotations

from typing import ClassVar

import pandas as pd
from sqlalchemy import URL, create_engine, text
from sqlalchemy.engine import Engine

from fhvi_ingestion.connectors.base import BaseConnector
from fhvi_ingestion.connectors.factory import register_connector


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


_TRUE = {"true", "yes", "1", "oui"}


@register_connector("sqlserver")
class SqlServerConnector(SqlAlchemyConnector):
    driver = "mssql+pymssql"
    required_keys = ("host", "database")

    def _build_url(self) -> URL:
        c = self.source.connection
        if str(c.get("driver", "pymssql")).lower() != "pyodbc":
            missing = [k for k in ("port", "user", "password") if not c.get(k)]
            if missing:
                raise ValueError(f"[{self.source.name}] connexion SQL Server (pymssql) : clés manquantes {missing}")
            return super()._build_url()

        query = {
            "driver": c.get("odbc_driver", "ODBC Driver 18 for SQL Server"),
            "TrustServerCertificate": "yes" if str(c.get("trust_server_certificate", "")).lower() in _TRUE else "no",
        }
        port = int(c["port"]) if c.get("port") else None
        if str(c.get("trusted_connection", "")).lower() in _TRUE:
            query["Trusted_Connection"] = "yes"
            return URL.create("mssql+pyodbc", host=c["host"], port=port, database=c["database"], query=query)
        return URL.create("mssql+pyodbc", username=c["user"], password=c["password"], host=c["host"],
                          port=port, database=c["database"], query=query)
