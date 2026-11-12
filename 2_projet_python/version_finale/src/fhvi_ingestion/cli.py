"""cli utilisant argparse (la variante click est dans exemples/cli_click.py)"""
from __future__ import annotations

import argparse
from datetime import date

from fhvi_ingestion import __version__

LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


# une erreur levée ici fait sortir argparse en code 2, le même que "config invalide"
def valid_date(value: str) -> str:
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        raise argparse.ArgumentTypeError(f"date invalide '{value}' (format attendu : AAAA-MM-JJ)") from None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fhvi-ingest",
        description="Ingère les sources décrites dans un fichier YAML vers la landing zone (bucket S3).",
        epilog=("Codes retour : 0 = succès, 1 = au moins une table en échec, 2 = configuration invalide.\n"
                "Exemples :\n"
                "  fhvi-ingest --sources dpi_nord --log-level DEBUG\n"
                "  fhvi-ingest --tables fact_ouest.prestations --load-date 2025-03-14   # rejouer une date\n"
                "  fhvi-ingest --rerun-failed 20261109T125942Z-608b18a7                 # rejouer les échecs"),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-c", "--config", default="config/pipeline.yaml",
                        help="Fichier de configuration YAML (défaut : config/pipeline.yaml).")
    # sources / tables / rerun-failed : une seule à la fois, argparse refuse le mélange
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument("-s", "--sources", nargs="+", metavar="SOURCE",
                       help="Sources à ingérer (défaut : toutes les sources 'enabled' du YAML).")
    scope.add_argument("-t", "--tables", nargs="+", metavar="SOURCE.TABLE",
                       help="Rejeu ciblé : uniquement ces tables (ex. fact_ouest.prestations).")
    scope.add_argument("--rerun-failed", metavar="RUN_ID",
                       help="Rejoue uniquement les tables en échec du run RUN_ID, à sa date de chargement "
                            "(lue dans son manifeste).")
    parser.add_argument("-d", "--load-date", type=valid_date, default=date.today().isoformat(),
                        help="Date logique de chargement (défaut : aujourd'hui).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Lit, transforme et journalise, sans rien écrire dans la destination.")
    parser.add_argument("--fail-fast", action="store_true",
                        help="Arrête le run à la première table en échec (défaut : on continue).")
    parser.add_argument("--list-sources", action="store_true",
                        help="Affiche les sources du YAML puis quitte.")
    # type est appliqué avant le check de choices -> "debug" en minuscules passe aussi
    parser.add_argument("-l", "--log-level", default="INFO", choices=LOG_LEVELS, type=str.upper,
                        help="Niveau de log (défaut : INFO).")
    parser.add_argument("--log-file", metavar="CHEMIN",
                        help="Écrit aussi les logs dans ce fichier (ex. logs/ingestion.log).")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    return build_parser().parse_args(argv)
