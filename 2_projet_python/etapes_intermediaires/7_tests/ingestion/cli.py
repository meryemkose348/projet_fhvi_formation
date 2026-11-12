"""cli de l'ingestion (argparse)"""
from __future__ import annotations

import argparse
from datetime import date


def valid_date(value: str) -> str:
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        raise argparse.ArgumentTypeError(f"date invalide '{value}' (format attendu : AAAA-MM-JJ)") from None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ingestion",
        description="Ingère les sources décrites dans un fichier YAML vers la destination configurée.",
        epilog="Exemple : python main.py --config config/pipeline.yaml --sources dpi_nord",
    )
    parser.add_argument(
        "-c", "--config",
        default="config/pipeline.yaml",
        help="Fichier de configuration YAML (défaut : config/pipeline.yaml).",
    )
    parser.add_argument(
        "-s", "--sources",
        nargs="+",
        metavar="SOURCE",
        help="Sources à ingérer (défaut : toutes les sources 'enabled' du YAML).",
    )
    parser.add_argument(
        "-d", "--load-date",
        type=valid_date,
        default=date.today().isoformat(),
        help="Date de chargement utilisée dans le chemin de destination (défaut : aujourd'hui).",
    )
    parser.add_argument("--dry-run", action="store_true", help="Lit les données sans rien écrire.")
    parser.add_argument("--list-sources", action="store_true", help="Affiche les sources du YAML puis quitte.")
    return parser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    return build_parser().parse_args(argv)
