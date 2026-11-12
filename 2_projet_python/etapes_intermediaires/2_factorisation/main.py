"""ingestion fhvi factorisée
"""
from __future__ import annotations

from datetime import date

import pandas as pd

from ingestion.extract import read_duckdb_table, read_sql_table
from ingestion.load import build_key, write_parquet
from ingestion.sources import SOURCES
from ingestion.transform import normalize


def extract(source: dict, table: str) -> pd.DataFrame:
    if source["kind"] == "sql":
        return read_sql_table(source["location"], table)
    if source["kind"] == "duckdb":
        return read_duckdb_table(source["location"], table)
    raise ValueError(f"Type de source inconnu : {source['kind']}")


def ingest_table(source: dict, table: str, load_date: str) -> int:
    df = normalize(extract(source, table))
    write_parquet(df, build_key(source["name"], table, load_date))
    return len(df)


def main() -> None:
    load_date = date.today().isoformat()
    for source in SOURCES:
        for table in source["tables"]:
            rows = ingest_table(source, table, load_date)
            print(f"{source['name']}.{table} : {rows} lignes")


if __name__ == "__main__":
    main()
