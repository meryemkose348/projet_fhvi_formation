"""Vérifie que les 4 sources et le bucket de destination sont accessibles.

Usage (depuis 3_environnement_docker/, venv du projet activé) :
    python scripts/check_env.py

Lit les paramètres dans 2_projet_python/.env (mêmes valeurs que le pipeline).
Code retour 0 si tout est OK, 1 sinon : utilisable dans un script ou une CI.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import boto3
import duckdb
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

PROJECT_DIR = Path(__file__).resolve().parents[2] / "2_projet_python"
load_dotenv(PROJECT_DIR / ".env")


def env(name: str) -> str:
    value = os.getenv(name)
    if value is None:
        sys.exit(f"[KO] Variable {name} absente : avez-vous copié 2_projet_python/.env.example en .env ?")
    return value


def check_sql(label: str, url: str, query: str) -> bool:
    try:
        engine = create_engine(url)
        with engine.connect() as con:
            n = con.execute(text(query)).scalar_one()
        print(f"[OK] {label:<32} {n} lignes")
        return True
    except Exception as exc:  # noqa: BLE001 - on veut afficher toute erreur
        print(f"[KO] {label:<32} {type(exc).__name__}: {str(exc).splitlines()[0]}")
        return False


def check_duckdb() -> bool:
    path = Path(env("DUCKDB_PATH"))
    if not path.is_absolute():
        path = (PROJECT_DIR / path).resolve()
    if not path.exists():
        print(f"[KO] DuckDB (pharmacie)              fichier absent : {path} -> lancez scripts/init_duckdb.py")
        return False
    with duckdb.connect(str(path), read_only=True) as con:
        n = con.execute("SELECT count(*) FROM dispensations").fetchone()[0]
    print(f"[OK] {'DuckDB (pharmacie)':<32} {n} lignes")
    return True


def check_s3() -> bool:
    try:
        s3 = boto3.client(
            "s3",
            endpoint_url=env("S3_ENDPOINT_URL"),
            aws_access_key_id=env("S3_ACCESS_KEY"),
            aws_secret_access_key=env("S3_SECRET_KEY"),
            region_name="us-east-1",
        )
        buckets = [b["Name"] for b in s3.list_buckets()["Buckets"]]
        bucket = env("S3_BUCKET")
        status = "OK" if bucket in buckets else "KO"
        print(f"[{status}] {'Bucket S3 (SeaweedFS)':<32} buckets={buckets}")
        return status == "OK"
    except Exception as exc:  # noqa: BLE001
        print(f"[KO] {'Bucket S3 (SeaweedFS)':<32} {type(exc).__name__}: {exc}")
        return False


def main() -> None:
    pg = (f"postgresql+psycopg://{env('PG_USER')}:{env('PG_PASSWORD')}"
          f"@{env('PG_HOST')}:{env('PG_PORT')}/{env('PG_DB')}")
    maria = (f"mysql+pymysql://{env('MARIADB_USER')}:{env('MARIADB_PASSWORD')}"
             f"@{env('MARIADB_HOST')}:{env('MARIADB_PORT')}/{env('MARIADB_DB')}")
    mssql = (f"mssql+pymssql://{env('MSSQL_USER')}:{env('MSSQL_PASSWORD')}"
             f"@{env('MSSQL_HOST')}:{env('MSSQL_PORT')}/{env('MSSQL_DB')}")
    results = [
        check_sql("PostgreSQL (dpi_nord)", pg, "SELECT count(*) FROM sejours"),
        check_sql("MariaDB (rdv_sud)", maria, "SELECT count(*) FROM RENDEZ_VOUS"),
        check_sql("SQL Server (FACTURATION_OUEST)", mssql, "SELECT count(*) FROM fact.Prestations"),
        check_duckdb(),
        check_s3(),
    ]
    print("\nEnvironnement prêt !" if all(results) else "\nAu moins un service est indisponible.")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
