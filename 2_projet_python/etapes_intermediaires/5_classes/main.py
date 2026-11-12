from __future__ import annotations

import sys

from ingestion.cli import parse_args
from ingestion.config import ConfigError, load_config
from ingestion.pipeline import IngestionPipeline


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        config = load_config(args.config)
        sources = config.select(args.sources)
    except ConfigError as exc:
        print(f"ERREUR DE CONFIGURATION : {exc}", file=sys.stderr)
        return 2

    if args.list_sources:
        for s in config.sources:
            state = "activée " if s.enabled else "désactivée"
            print(f"{s.name:<12} {s.type:<9} {state}  tables={[t.name for t in s.tables]}")
        return 0

    pipeline = IngestionPipeline(config, load_date=args.load_date, dry_run=args.dry_run)
    for result in pipeline.run(sources):
        print(f"{result.source}.{result.table:<15} {result.rows:>6} lignes -> {result.uri}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
