from __future__ import annotations

import os
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from dotenv import find_dotenv, load_dotenv

_ENV_PATTERN = re.compile(r"\$\{([A-Z0-9_]+)\}")
_ENV_FILE = find_dotenv(usecwd=True)
load_dotenv(_ENV_FILE)
ENV_BASE_DIR = Path(_ENV_FILE).parent if _ENV_FILE else Path.cwd()


class ConfigError(Exception):
    """le msg regroupe toutes les erreurs trouvées, pas juste la première"""


@dataclass(frozen=True)
class TableConfig:
    name: str
    target: str
    query: str | None = None

    @property
    def sql(self) -> str:
        return self.query or f"SELECT * FROM {self.name}"


@dataclass(frozen=True)
class SourceConfig:
    name: str
    type: str
    connection: dict[str, Any]
    tables: list[TableConfig]
    enabled: bool = True
    description: str = ""


@dataclass(frozen=True)
class DestinationConfig:
    type: str
    format: str = "parquet"
    prefix: str = "raw"
    bucket: str | None = None
    path: str | None = None
    endpoint_url: str | None = None
    access_key: str | None = None
    secret_key: str | None = None


@dataclass(frozen=True)
class PipelineConfig:
    destination: DestinationConfig
    sources: list[SourceConfig] = field(default_factory=list)

    def source_names(self) -> list[str]:
        return [s.name for s in self.sources]

    def select(self, names: list[str] | None = None) -> list[SourceConfig]:
        if not names:
            return [s for s in self.sources if s.enabled]
        unknown = sorted(set(names) - set(self.source_names()))
        if unknown:
            raise ConfigError(f"source(s) inconnue(s) : {unknown} - disponibles : {self.source_names()}")
        return [s for s in self.sources if s.name in names]


def interpolate_env(value: Any, errors: list[str]) -> Any:
    if isinstance(value, dict):
        return {k: interpolate_env(v, errors) for k, v in value.items()}
    if isinstance(value, list):
        return [interpolate_env(v, errors) for v in value]
    if isinstance(value, str):
        def replace(match: re.Match) -> str:
            name = match.group(1)
            if name not in os.environ:
                errors.append(f"variable d'environnement absente : ${{{name}}}")
                return ""
            return os.environ[name]
        return _ENV_PATTERN.sub(replace, value)
    return value


def validate_config(
    config: dict,
    source_types: Mapping[str, Sequence[str]],
    destination_types: Mapping[str, Sequence[str]],
    formats: Iterable[str],
) -> list[str]:
    errors: list[str] = []
    formats = set(formats)
    destination = config.get("destination") or {}
    dest_type = destination.get("type")
    if dest_type not in destination_types:
        errors.append(f"destination.type '{dest_type}' inconnu (attendu : {sorted(destination_types)})")
    else:
        for key in destination_types[dest_type]:
            if not destination.get(key):
                errors.append(f"destination.{key} est obligatoire pour une destination '{dest_type}'")
    if destination.get("format", "parquet") not in formats:
        errors.append(f"destination.format '{destination.get('format')}' non supporté (attendu : {sorted(formats)})")

    sources = config.get("sources")
    if not isinstance(sources, list) or not sources:
        return errors + ["la section 'sources' doit contenir au moins une source"]
    seen: set[str] = set()
    for i, source in enumerate(sources):
        label = f"sources[{i}] ({source.get('name', '?')})"
        if not source.get("name"):
            errors.append(f"{label} : 'name' est obligatoire")
        elif source["name"] in seen:
            errors.append(f"{label} : nom de source en doublon")
        seen.add(source.get("name"))
        if source.get("type") not in source_types:
            errors.append(f"{label} : type '{source.get('type')}' inconnu (attendu : {sorted(source_types)})")
        else:
            connection = source.get("connection") or {}
            for key in source_types[source["type"]]:
                if not connection.get(key):
                    errors.append(f"{label} : connection.{key} est obligatoire pour le type '{source['type']}'")
        tables = source.get("tables")
        if not isinstance(tables, list) or not tables:
            errors.append(f"{label} : 'tables' doit contenir au moins une table")
        elif any(not isinstance(t, dict) or not t.get("name") for t in tables):
            errors.append(f"{label} : chaque table doit avoir un 'name'")
    return errors


def _to_source(raw: dict) -> SourceConfig:
    connection = dict(raw["connection"])
    if "path" in connection:
        connection["path"] = str((ENV_BASE_DIR / connection["path"]).resolve())
    tables = [TableConfig(name=t["name"], target=t.get("target", t["name"].lower()), query=t.get("query"))
              for t in raw["tables"]]
    return SourceConfig(name=raw["name"], type=raw["type"], connection=connection, tables=tables,
                        enabled=raw.get("enabled", True), description=raw.get("description", ""))


def load_config(
    path: str | Path,
    source_types: Mapping[str, Sequence[str]],
    destination_types: Mapping[str, Sequence[str]],
    formats: Iterable[str],
) -> PipelineConfig:
    path = Path(path)
    if not path.exists():
        raise ConfigError(f"fichier de configuration introuvable : {path}")
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise ConfigError(f"YAML mal formé dans {path} : {exc}") from exc
    errors: list[str] = []
    raw = interpolate_env(raw, errors)
    errors += validate_config(raw, source_types, destination_types, formats)
    if errors:
        raise ConfigError(f"{len(errors)} erreur(s) dans {path} :\n  - " + "\n  - ".join(errors))
    return PipelineConfig(
        destination=DestinationConfig(**raw["destination"]),
        sources=[_to_source(s) for s in raw["sources"]],
    )
