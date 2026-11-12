"""pour comparer argparse et click : même interface que cli.py, écrite avec click

argparse (bibliothèque standard, aucune dépendance) est utilisé dans le projet
click est l'autre choix courant. 
Ses atouts : des décorateurs lisibles, des types prêts à l'emploi (Path, DateTime, Choice) et
surtout les SOUS-COMMANDES, pratiques quand un outil fait plusieurs choses comme :

    python exemples/cli_click.py run -s dpi_nord -s fact_ouest --dry-run
    python exemples/cli_click.py rerun 20261109T125942Z-608b18a7
    python exemples/cli_click.py tables fact_ouest.prestations --load-date 2025-03-14
    python exemples/cli_click.py list-sources
    python exemples/cli_click.py --help

Choisir soit lui soit argparse par projet
Ici, click ne fait que traduire ses options en
arguments pour l'application existante : le cœur (app.main) ne change pas
"""
from __future__ import annotations

import click

from fhvi_ingestion.app import main as run_app

CONFIG = click.option("-c", "--config", default="config/pipeline.yaml", show_default=True,
                      type=click.Path(exists=True, dir_okay=False), help="Fichier de configuration YAML.")
LOAD_DATE = click.option("-d", "--load-date", type=click.DateTime(formats=["%Y-%m-%d"]), default=None,
                         help="Date logique de chargement AAAA-MM-JJ (défaut : aujourd'hui).")
DRY_RUN = click.option("--dry-run", is_flag=True, help="Lit et journalise sans rien écrire.")
LOG_LEVEL = click.option("-l", "--log-level", default="INFO", show_default=True,
                         type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], case_sensitive=False))


# options partagées -> liste d'arguments façon argparse
def _common(config, load_date, dry_run, log_level) -> list[str]:
    argv = ["--config", config, "--log-level", log_level.upper()]
    if load_date:
        argv += ["--load-date", load_date.date().isoformat()]
    if dry_run:
        argv.append("--dry-run")
    return argv


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
def cli() -> None:
    """ingestion du yml vers le s3"""


@cli.command()
@CONFIG
@click.option("-s", "--sources", multiple=True, metavar="SOURCE", help="Source à ingérer (répétable).")
@LOAD_DATE
@DRY_RUN
@LOG_LEVEL
def run(config, sources, load_date, dry_run, log_level) -> None:
    argv = _common(config, load_date, dry_run, log_level)
    if sources:
        argv += ["--sources", *sources]
    raise SystemExit(run_app(argv))


@cli.command()
@CONFIG
@click.argument("tables", nargs=-1, required=True)
@LOAD_DATE
@DRY_RUN
@LOG_LEVEL
def tables(config, tables, load_date, dry_run, log_level) -> None:
    raise SystemExit(run_app(_common(config, load_date, dry_run, log_level) + ["--tables", *tables]))


@cli.command()
@CONFIG
@click.argument("run_id")
@DRY_RUN
@LOG_LEVEL
def rerun(config, run_id, dry_run, log_level) -> None:
    raise SystemExit(run_app(_common(config, None, dry_run, log_level) + ["--rerun-failed", run_id]))


@cli.command("list-sources")
@CONFIG
def list_sources(config) -> None:
    raise SystemExit(run_app(["--config", config, "--list-sources"]))


if __name__ == "__main__":
    cli()
