"""Écriture des résultats dans le bucket S3 de destination"""
from __future__ import annotations

import io

import boto3
import pandas as pd

from ingestion import settings


def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT_URL,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
        region_name="us-east-1",   # boto3 veut une région, avec un endpoint perso la valeur importe peu
    )


def write_parquet(df: pd.DataFrame, key: str) -> None:
    # tout se passe en mémoire, pas de fichier temporaire sur le disque
    buffer = io.BytesIO()
    df.to_parquet(buffer, index=False)
    get_s3_client().put_object(Bucket=settings.S3_BUCKET, Key=key, Body=buffer.getvalue())
