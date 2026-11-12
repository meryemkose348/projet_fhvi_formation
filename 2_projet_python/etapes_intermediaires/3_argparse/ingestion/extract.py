"""extraction générique où on a une fonction par techno désormais, et plus une par table"""
from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd
from sqlalchemy import create_engine


def read_sql_table(url: str, table: str) -> pd.DataFrame:
    engine = create_engine(url)
    try:
        return pd.read_sql(f"SELECT * FROM {table}", engine)
    finally:
        engine.dispose() 


def read_duckdb_table(path: Path, table: str) -> pd.DataFrame:
    with duckdb.connect(str(path), read_only=True) as con:
        return con.execute(f"SELECT * FROM {table}").df()
