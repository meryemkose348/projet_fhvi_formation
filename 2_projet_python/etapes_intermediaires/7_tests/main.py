from __future__ import annotations

import sys

from ingestion.cli import parse_args
from ingestion.config import ConfigError, load_config
from ingestion.connectors import available_connectors
from ingestion.pipeline import IngestionPipeline
from ingestion.writers import FORMATS, DatasetWriter, available_storages, build_storage, get_format


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        config = load_config(args.config, available_connectors(), available_storages(), FORMATS)
        sources = config.select(args.sources)
    except ConfigError as exc:
        print(f"ERREUR DE CONFIGURATION : {exc}", file=sys.stderr)
        return 2

    if args.list_sources:
        for s in config.sources:
            state = "activée " if s.enabled else "désactivée"
            print(f"{s.name:<12} {s.type:<9} {state}  tables={[t.name for t in s.tables]}")
        return 0

    destination = config.destination
    writer = DatasetWriter(
        storage=build_storage(destination, dry_run=args.dry_run),
        file_format=get_format(destination.format),
        prefix=destination.prefix,
    )
    pipeline = IngestionPipeline(writer, load_date=args.load_date)
    for result in pipeline.run(sources):
        print(f"{result.source}.{result.table:<15} {result.rows:>6} lignes -> {result.uri}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
