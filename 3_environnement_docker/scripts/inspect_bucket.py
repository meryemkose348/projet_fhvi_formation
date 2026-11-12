"""Explore le bucket de destination : liste les fichiers et affiche un aperçu.

Usage (depuis 3_environnement_docker/, venv du projet activé) :
    python scripts/inspect_bucket.py                       # liste tous les objets
    python scripts/inspect_bucket.py --prefix raw/dpi_nord # filtre par préfixe
    python scripts/inspect_bucket.py --show raw/dpi_nord/patients/.../patients.parquet
    python scripts/inspect_bucket.py --show-latest sejours # dernier fichier contenant "sejours"
    python scripts/inspect_bucket.py --purge               # vide le bucket (démo / reset)
"""
from __future__ import annotations

import argparse
import io
import os
from pathlib import Path

import boto3
import pandas as pd
from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).resolve().parents[2] / "2_projet_python"
load_dotenv(PROJECT_DIR / ".env")


def client():
    return boto3.client(
        "s3",
        endpoint_url=os.environ["S3_ENDPOINT_URL"],
        aws_access_key_id=os.environ["S3_ACCESS_KEY"],
        aws_secret_access_key=os.environ["S3_SECRET_KEY"],
        region_name="us-east-1",
    )


def list_objects(s3, bucket: str, prefix: str = "") -> list[dict]:
    paginator = s3.get_paginator("list_objects_v2")
    objects: list[dict] = []
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        objects.extend(page.get("Contents", []))
    return objects


def show(s3, bucket: str, key: str, rows: int) -> None:
    body = s3.get_object(Bucket=bucket, Key=key)["Body"].read()
    if key.endswith(".parquet"):
        df = pd.read_parquet(io.BytesIO(body))
    elif key.endswith(".csv"):
        df = pd.read_csv(io.BytesIO(body))
    else:
        print(body.decode("utf-8"))
        return
    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 20)
    print(f"\n=== {key} : {len(df)} lignes x {len(df.columns)} colonnes ===")
    print(df.dtypes.to_string())
    print()
    print(df.head(rows).to_string())


def main() -> None:
    parser = argparse.ArgumentParser(description="Explore le bucket S3 de la formation.")
    parser.add_argument("--bucket", default=os.getenv("S3_BUCKET", "fhvi-landing"))
    parser.add_argument("--prefix", default="", help="Filtre sur le début de la clé.")
    parser.add_argument("--show", metavar="KEY", help="Affiche le contenu d'un fichier.")
    parser.add_argument("--show-latest", metavar="MOTIF", help="Affiche le fichier le plus récent contenant MOTIF.")
    parser.add_argument("--rows", type=int, default=5, help="Nombre de lignes affichées (défaut : 5).")
    parser.add_argument("--purge", action="store_true", help="Supprime tous les objets du bucket.")
    args = parser.parse_args()

    s3 = client()
    objects = list_objects(s3, args.bucket, args.prefix)

    if args.purge:
        for obj in objects:
            s3.delete_object(Bucket=args.bucket, Key=obj["Key"])
        print(f"{len(objects)} objet(s) supprimé(s) de s3://{args.bucket}/{args.prefix}")
        return
    if args.show:
        show(s3, args.bucket, args.show, args.rows)
        return
    if args.show_latest:
        matching = [o for o in objects if args.show_latest in o["Key"] and not o["Key"].endswith(".json")]
        if not matching:
            print(f"Aucun fichier ne contient '{args.show_latest}'.")
            return
        latest = max(matching, key=lambda o: o["LastModified"])
        show(s3, args.bucket, latest["Key"], args.rows)
        return

    print(f"s3://{args.bucket}/{args.prefix}  ({len(objects)} objet(s))")
    for obj in sorted(objects, key=lambda o: o["Key"]):
        print(f"  {obj['LastModified']:%Y-%m-%d %H:%M:%S}  {obj['Size']:>9} o  {obj['Key']}")


if __name__ == "__main__":
    main()
