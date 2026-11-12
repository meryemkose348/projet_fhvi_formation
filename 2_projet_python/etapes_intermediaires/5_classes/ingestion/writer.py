from __future__ import annotations

import io
from pathlib import Path

import boto3
import pandas as pd

from ingestion.config import DestinationConfig


def serialize(df: pd.DataFrame, fmt: str) -> bytes:
    if fmt == "parquet":
        buffer = io.BytesIO()
        df.to_parquet(buffer, index=False)
        return buffer.getvalue()
    if fmt == "csv":
        return df.to_csv(index=False).encode("utf-8")
    raise ValueError(f"Format non supporté : {fmt}")


class DatasetWriter:
    def __init__(self, destination: DestinationConfig) -> None:
        self.destination = destination
        self._s3 = None
        if destination.type == "s3":
            self._s3 = boto3.client(
                "s3",
                endpoint_url=destination.endpoint_url,
                aws_access_key_id=destination.access_key,
                aws_secret_access_key=destination.secret_key,
                region_name="us-east-1",
            )

    def build_key(self, source: str, table: str, load_date: str) -> str:
        d = self.destination
        return f"{d.prefix}/{source}/{table}/{load_date}/{table}.{d.format}"

    def write(self, df: pd.DataFrame, source: str, table: str, load_date: str) -> str:
        key = self.build_key(source, table, load_date)
        body = serialize(df, self.destination.format)
        if self.destination.type == "s3":
            self._s3.put_object(Bucket=self.destination.bucket, Key=key, Body=body)
            return f"s3://{self.destination.bucket}/{key}"
        target = Path(self.destination.path) / key
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(body)
        return str(target)
