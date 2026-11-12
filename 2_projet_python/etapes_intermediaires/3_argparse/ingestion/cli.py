"""utilsiation de cli avec argparse"""
from __future__ import annotations

import argparse
from datetime import date

from ingestion.sources import SOURCES

# sert pour choices= : argparse rejette tout seul une source qui n'exsite pas
SOURCE_NAMES = [source["name"] for source in SOURCES]


def valid_date(value: str) -> str:
    # passé en type= : une date invalide donne un message argparse propre, pas une stacktrace
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        raise argparse.ArgumentTypeError(f"date invalide '{value}' (format attendu : AAAA-MM-JJ)") from None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ingestion",
        description="Ingère les tables des sources FHVI vers le bucket de destination.",
        epilog="Exemple : python main.py --sources dpi_nord rdv_sud --load-date 2026-11-01",
    )
    parser.add_argument(
        "-s", "--sources",
        nargs="+",
        choices=SOURCE_NAMES,
        default=SOURCE_NAMES,
        metavar="SOURCE",
        help=f"Sources à ingérer parmi {', '.join(SOURCE_NAMES)} (défaut : toutes).",
    )
    parser.add_argument(
        "-d", "--load-date",
        type=valid_date,
        default=date.today().isoformat(),
        help="Date de chargement utilisée dans le chemin de destination (défaut : aujourd'hui).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Lit et normalise les données sans rien écrire dans le bucket.",
    )
    parser.add_argument(
        "--list-sources",
        action="store_true",
        help="Affiche les sources disponibles puis quitte.",
    )
    return parser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    return build_parser().parse_args(argv)
