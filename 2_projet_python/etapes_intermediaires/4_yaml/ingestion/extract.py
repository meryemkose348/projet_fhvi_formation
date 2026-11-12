"""extraction générique, pilotée par le bloc de config de la source"""
from __future__ import annotations

import duckdb
import pandas as pd
from sqlalchemy import create_engine

SQLALCHEMY_DRIVERS = {
    "postgres": "postgresql+psycopg",
    "mariadb": "mysql+pymysql",
    "sqlserver": "mssql+pymssql",
}


def build_sqlalchemy_url(source_type: str, connection: dict) -> str:
    # TODO passer par URL.create : là un @ ou un : dans le mot de passe casse l'URL
    driver = SQLALCHEMY_DRIVERS[source_type]
    return (f"{driver}://{connection['user']}:{connection['password']}"
            f"@{connection['host']}:{connection['port']}/{connection['database']}")


def build_query(table: dict) -> str:
    return table.get("query") or f"SELECT * FROM {table['name']}"


def extract(source: dict, table: dict) -> pd.DataFrame:
    query = build_query(table)
    if source["type"] in SQLALCHEMY_DRIVERS:
        engine = create_engine(build_sqlalchemy_url(source["type"], source["connection"]))
        try:
            return pd.read_sql(query, engine)
        finally:
            engine.dispose()
    if source["type"] == "duckdb":
        with duckdb.connect(source["connection"]["path"], read_only=True) as con:
            return con.execute(query).df()
    raise ValueError(f"Type de source non géré : {source['type']}")
