"""écriture vers s3"""
from __future__ import annotations

import io
from pathlib import Path

import boto3
import pandas as pd


def build_key(prefix: str, source: str, table: str, load_date: str, fmt: str) -> str:
    return f"{prefix}/{source}/{table}/{load_date}/{table}.{fmt}"


def serialize(df: pd.DataFrame, fmt: str) -> bytes:
    if fmt == "parquet":
        buffer = io.BytesIO()
        df.to_parquet(buffer, index=False)
        return buffer.getvalue()
    if fmt == "csv":
        return df.to_csv(index=False).encode("utf-8")
    raise ValueError(f"Format non supporté : {fmt}")


def write(df: pd.DataFrame, destination: dict, key: str) -> str:
    # chaque nouveau format ou destination = un if de plus ici et dans serialize() etc
    # c'est exactement ce que le Strategy Pattern va régler
    body = serialize(df, destination["format"])
    if destination["type"] == "s3":
        client = boto3.client(
            "s3",
            endpoint_url=destination.get("endpoint_url"),
            aws_access_key_id=destination.get("access_key"),
            aws_secret_access_key=destination.get("secret_key"),
            region_name="us-east-1",
        )
        client.put_object(Bucket=destination["bucket"], Key=key, Body=body)
        return f"s3://{destination['bucket']}/{key}"
    if destination["type"] == "local":
        target = Path(destination["path"]) / key
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(body)
        return str(target)
    raise ValueError(f"Destination non supportée : {destination['type']}")
