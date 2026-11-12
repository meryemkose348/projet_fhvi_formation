from __future__ import annotations

import pandas as pd

from ingestion.cli import parse_args
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


def ingest_table(source: dict, table: str, load_date: str, dry_run: bool = False) -> int:
    df = normalize(extract(source, table))
    key = build_key(source["name"], table, load_date)
    if dry_run:
        print(f"  [dry-run] aurait écrit s3://.../{key}")
    else:
        write_parquet(df, key)
    return len(df)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    if args.list_sources:
        for source in SOURCES:
            print(f"{source['name']:<10} ({source['kind']}) : {', '.join(source['tables'])}")
        return

    selected = [s for s in SOURCES if s["name"] in args.sources]
    for source in selected:
        for table in source["tables"]:
            rows = ingest_table(source, table, args.load_date, args.dry_run)
            print(f"{source['name']}.{table} : {rows} lignes")


if __name__ == "__main__":
    main()
