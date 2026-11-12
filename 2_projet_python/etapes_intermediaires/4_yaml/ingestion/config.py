"""chargement + validation du yml du pipeline en 3 temps : lecture, remplacement des ${VARIABLES}, puis vérif de cohérence
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml
from dotenv import find_dotenv, load_dotenv

SUPPORTED_SOURCE_TYPES = {
    "postgres": ["host", "port", "database", "user", "password"],
    "mariadb": ["host", "port", "database", "user", "password"],
    "sqlserver": ["host", "port", "database", "user", "password"],
    "duckdb": ["path"],
}
SUPPORTED_DESTINATIONS = {"s3": ["bucket"], "local": ["path"]}
SUPPORTED_FORMATS = {"parquet", "csv"}

_ENV_PATTERN = re.compile(r"\$\{([A-Z0-9_]+)\}")

_ENV_FILE = find_dotenv(usecwd=True)
load_dotenv(_ENV_FILE)
ENV_BASE_DIR = Path(_ENV_FILE).parent if _ENV_FILE else Path.cwd()


class ConfigError(Exception):
    """config invalide"""


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


def validate_config(config: dict) -> list[str]:
    errors: list[str] = []
    destination = config.get("destination") or {}
    dest_type = destination.get("type")
    if dest_type not in SUPPORTED_DESTINATIONS:
        errors.append(f"destination.type '{dest_type}' inconnu (attendu : {sorted(SUPPORTED_DESTINATIONS)})")
    else:
        for key in SUPPORTED_DESTINATIONS[dest_type]:
            if not destination.get(key):
                errors.append(f"destination.{key} est obligatoire pour une destination '{dest_type}'")
    if destination.get("format", "parquet") not in SUPPORTED_FORMATS:
        errors.append(f"destination.format '{destination.get('format')}' non supporté "
                      f"(attendu : {sorted(SUPPORTED_FORMATS)})")

    sources = config.get("sources")
    if not isinstance(sources, list) or not sources:
        errors.append("la section 'sources' doit contenir au moins une source")
        return errors

    seen: set[str] = set()
    for i, source in enumerate(sources):
        label = f"sources[{i}] ({source.get('name', '?')})"
        name = source.get("name")
        if not name:
            errors.append(f"{label} : 'name' est obligatoire")
        elif name in seen:
            errors.append(f"{label} : nom de source en doublon")
        seen.add(name)

        source_type = source.get("type")
        if source_type not in SUPPORTED_SOURCE_TYPES:
            errors.append(f"{label} : type '{source_type}' inconnu (attendu : {sorted(SUPPORTED_SOURCE_TYPES)})")
        else:
            connection = source.get("connection") or {}
            for key in SUPPORTED_SOURCE_TYPES[source_type]:
                if not connection.get(key):
                    errors.append(f"{label} : connection.{key} est obligatoire pour le type '{source_type}'")

        tables = source.get("tables")
        if not isinstance(tables, list) or not tables:
            errors.append(f"{label} : 'tables' doit contenir au moins une table")
        else:
            for table in tables:
                if not isinstance(table, dict) or not table.get("name"):
                    errors.append(f"{label} : chaque table doit avoir un 'name'")
    return errors


def load_config(path: str | Path) -> dict:
    path = Path(path)
    if not path.exists():
        raise ConfigError(f"fichier de configuration introuvable : {path}")
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise ConfigError(f"YAML mal formé dans {path} : {exc}") from exc

    errors: list[str] = []
    config = interpolate_env(raw, errors)
    errors += validate_config(config)
    if errors:
        details = "\n  - ".join(errors)
        raise ConfigError(f"{len(errors)} erreur(s) dans {path} :\n  - {details}")

    config["destination"].setdefault("prefix", "raw")
    config["destination"].setdefault("format", "parquet")
    for source in config["sources"]:
        source.setdefault("enabled", True)
        if source["type"] == "duckdb":
            source["connection"]["path"] = str((ENV_BASE_DIR / source["connection"]["path"]).resolve())
    return config
