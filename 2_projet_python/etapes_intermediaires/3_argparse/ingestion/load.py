"""passage dans le s3"""
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
        region_name="us-east-1",
    )


def build_key(source: str, table: str, load_date: str) -> str:
    name = table.split(".")[-1].lower()
    return f"raw/{source}/{name}/{load_date}/{name}.parquet"


def write_parquet(df: pd.DataFrame, key: str) -> None:
    buffer = io.BytesIO()
    df.to_parquet(buffer, index=False)
    get_s3_client().put_object(Bucket=settings.S3_BUCKET, Key=key, Body=buffer.getvalue())
