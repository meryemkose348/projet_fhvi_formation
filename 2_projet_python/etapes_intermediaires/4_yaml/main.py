"""Ingestion FHVI, étape 4 : tout ce qui décrit les sources passe dans un yml
"""
from __future__ import annotations

import sys

from ingestion.cli import parse_args
from ingestion.config import ConfigError, load_config
from ingestion.extract import extract
from ingestion.load import build_key, write
from ingestion.transform import normalize


def select_sources(config: dict, requested: list[str] | None) -> list[dict]:
    if not requested:
        return [s for s in config["sources"] if s["enabled"]]
    known = {s["name"]: s for s in config["sources"]}
    unknown = [name for name in requested if name not in known]
    if unknown:
        raise ConfigError(f"source(s) inconnue(s) : {unknown} - disponibles : {sorted(known)}")
    return [known[name] for name in requested]


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        config = load_config(args.config)
        sources = select_sources(config, args.sources)
    except ConfigError as exc:
        print(f"ERREUR DE CONFIGURATION : {exc}", file=sys.stderr)
        return 2 

    if args.list_sources:
        for s in config["sources"]:
            state = "activée " if s["enabled"] else "désactivée"
            print(f"{s['name']:<12} {s['type']:<9} {state}  tables={[t['name'] for t in s['tables']]}")
        return 0

    destination = config["destination"]
    for source in sources:
        for table in source["tables"]:
            target = table.get("target", table["name"].lower())
            df = normalize(extract(source, table))
            key = build_key(destination["prefix"], source["name"], target, args.load_date, destination["format"])
            uri = "(dry-run)" if args.dry_run else write(df, destination, key)
            print(f"{source['name']}.{table['name']:<15} {len(df):>6} lignes -> {uri}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
