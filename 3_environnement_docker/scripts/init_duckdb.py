"""Construit (ou reconstruit) la source DuckDB `data/pharmacie.duckdb`.

Usage (depuis 3_environnement_docker/) :
    python scripts/init_duckdb.py            # crée le fichier s'il n'existe pas
    python scripts/init_duckdb.py --force    # le recrée à partir de sql/duckdb/init.sql
"""
from __future__ import annotations

import argparse
from pathlib import Path

import duckdb

KIT_DIR = Path(__file__).resolve().parent.parent
SQL_FILE = KIT_DIR / "sql" / "duckdb" / "init.sql"
DB_FILE = KIT_DIR / "data" / "pharmacie.duckdb"


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialise la source DuckDB de la formation.")
    parser.add_argument("--force", action="store_true", help="Supprime et recrée le fichier.")
    args = parser.parse_args()

    if DB_FILE.exists() and not args.force:
        print(f"[OK] {DB_FILE} existe déjà (utilisez --force pour le recréer).")
        return

    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    DB_FILE.unlink(missing_ok=True)
    with duckdb.connect(str(DB_FILE)) as con:
        con.execute(SQL_FILE.read_text(encoding="utf-8"))
        for table in ("produits", "dispensations"):
            count = con.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            print(f"[OK] {table}: {count} lignes")
    print(f"[OK] Source DuckDB prête : {DB_FILE}")


if __name__ == "__main__":
    main()
