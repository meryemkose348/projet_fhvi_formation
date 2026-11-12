from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

import boto3

from fhvi_ingestion.config import DestinationConfig


class Storage(ABC):
    dry_run = False

    @abstractmethod
    def put(self, key: str, body: bytes) -> str:
        """renvoie l'uri de l'objet écrit"""

    @abstractmethod
    def list_keys(self, prefix: str) -> list[str]:
        """clés qui commencent par prefix, triées"""

    @abstractmethod
    def get(self, key: str) -> bytes:
        """FileNotFoundError si absent"""

    @abstractmethod
    def delete(self, key: str) -> None:
        """pas d'erreur si l'objet n'existe déjà plus"""


class S3Storage(Storage):
    def __init__(self, bucket: str, client) -> None:
        self.bucket = bucket
        self._client = client

    @classmethod
    def from_config(cls, destination: DestinationConfig) -> S3Storage:
        # region random pour boto3, SeaweedFS l'ignore mais obligé de li'nésérer dans la config
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

    def list_keys(self, prefix: str) -> list[str]:
        # list_objects_v2 s'arrête à 1000 clés par appel, d'où le paginator
        keys: list[str] = []
        for page in self._client.get_paginator("list_objects_v2").paginate(Bucket=self.bucket, Prefix=prefix):
            keys.extend(obj["Key"] for obj in page.get("Contents", []))
        return sorted(keys)

    def get(self, key: str) -> bytes:
        try:
            return self._client.get_object(Bucket=self.bucket, Key=key)["Body"].read()
        except self._client.exceptions.NoSuchKey:
            raise FileNotFoundError(f"s3://{self.bucket}/{key}") from None

    def delete(self, key: str) -> None:
        self._client.delete_object(Bucket=self.bucket, Key=key)


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

    def list_keys(self, prefix: str) -> list[str]:
        if not self.root.exists():
            return []
        keys = (p.relative_to(self.root).as_posix() for p in self.root.rglob("*") if p.is_file())
        return sorted(k for k in keys if k.startswith(prefix))

    def get(self, key: str) -> bytes:
        target = self.root / key
        if not target.is_file():
            raise FileNotFoundError(str(target))
        return target.read_bytes()

    def delete(self, key: str) -> None:
        (self.root / key).unlink(missing_ok=True)


# n'écrit ni ne supprime rien, mais les lectures passent au vrai stockage
class DryRunStorage(Storage):
    dry_run = True

    def __init__(self, inner: Storage | None = None) -> None:
        self.inner = inner

    def put(self, key: str, body: bytes) -> str:
        return f"(dry-run) {key} [{len(body)} octets]"

    def list_keys(self, prefix: str) -> list[str]:
        return self.inner.list_keys(prefix) if self.inner else []

    def get(self, key: str) -> bytes:
        if not self.inner:
            raise FileNotFoundError(key)
        return self.inner.get(key)

    def delete(self, key: str) -> None:
        return None


# type de destination -> la fabrique, avec les clés obligatoires dans le yml
STORAGES = {
    "s3": (S3Storage.from_config, ("bucket",)),
    "local": (LocalStorage.from_config, ("path",)),
}


def available_storages() -> dict[str, tuple[str, ...]]:
    return {name: keys for name, (_, keys) in STORAGES.items()}


def build_storage(destination: DestinationConfig, dry_run: bool = False) -> Storage:
    factory, _ = STORAGES[destination.type]
    storage = factory(destination)
    return DryRunStorage(inner=storage) if dry_run else storage
