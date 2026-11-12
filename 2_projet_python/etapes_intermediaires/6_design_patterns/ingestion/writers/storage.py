"""lieu de stockage avec le --dry-run devient une stratégie (DryRunStorage) au lieu de if éparpillés
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

import boto3

from ingestion.config import DestinationConfig


class Storage(ABC):
    @abstractmethod
    def put(self, key: str, body: bytes) -> str:
        """stocke body en key, et return l'uri écrite"""


class S3Storage(Storage):
    def __init__(self, bucket: str, client) -> None:
        self.bucket = bucket
        self._client = client

    @classmethod
    def from_config(cls, destination: DestinationConfig) -> S3Storage:
        client = boto3.client(
            "s3",
            endpoint_url=destination.endpoint_url,
            aws_access_key_id=destination.access_key,
            aws_secret_access_key=destination.secret_key,
            region_name="us-east-1",
        )
        return cls(destination.bucket, client)

    def put(self, key: str, body: bytes) -> str:
        self._client.put_object(Bucket=self.bucket, Key=key, Body=body)
        return f"s3://{self.bucket}/{key}"


class LocalStorage(Storage):
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    @classmethod
    def from_config(cls, destination: DestinationConfig) -> LocalStorage:
        return cls(destination.path)

    def put(self, key: str, body: bytes) -> str:
        target = self.root / key
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(body)
        return str(target)


class DryRunStorage(Storage):
    def put(self, key: str, body: bytes) -> str:
        return f"(dry-run) {key} [{len(body)} octets]"


# type de destination -> (fabrique, clés obligatoires ds le yml)
STORAGES = {
    "s3": (S3Storage.from_config, ("bucket",)),
    "local": (LocalStorage.from_config, ("path",)),
}


def available_storages() -> dict[str, tuple[str, ...]]:
    return {name: keys for name, (_, keys) in STORAGES.items()}


def build_storage(destination: DestinationConfig, dry_run: bool = False) -> Storage:
    if dry_run:
        return DryRunStorage()
    factory, _ = STORAGES[destination.type]
    return factory(destination)
