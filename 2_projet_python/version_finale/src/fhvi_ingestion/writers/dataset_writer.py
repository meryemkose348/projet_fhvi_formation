"""writer = un format + un stockage avec un rangement dans le bucket en partition

idempotence mise en place : comme le run_id est dans le nom du fichier, un rejeu ajouterait sinon un 2e fichier dans la partition 
et dbt / Tableau compteraient tout en double
Donc en overwrite_partition (défaut) on écrit d'abord le nouveau fichier, puis on delete les anciens de la partition : 
à aucun moment elle n'est vide
Les manifestes ne sont jamais supprimés, on garde l'historique de tous les runs
append (pas de suppression) = seulement pour des données vraiment additives, type journaux/événements
"""
from __future__ import annotations

import json
import logging

import pandas as pd

from fhvi_ingestion.report import RunReport
from fhvi_ingestion.run_context import RunContext
from fhvi_ingestion.writers.formats import FileFormat
from fhvi_ingestion.writers.storage import Storage

logger = logging.getLogger(__name__)

WRITE_MODES = ("overwrite_partition", "append")


class DatasetWriter:
    def __init__(self, storage: Storage, file_format: FileFormat, prefix: str = "raw",
                 write_mode: str = "overwrite_partition") -> None:
        if write_mode not in WRITE_MODES:
            raise ValueError(f"write_mode '{write_mode}' inconnu (attendu : {WRITE_MODES})")
        self.storage = storage
        self.file_format = file_format
        self.prefix = prefix
        self.write_mode = write_mode

    def partition(self, source: str, table: str, run: RunContext) -> str:
        return f"{self.prefix}/{source}/{table}/load_date={run.load_date}/"

    def build_key(self, source: str, table: str, run: RunContext) -> str:
        return f"{self.partition(source, table, run)}{table}__{run.run_id}.{self.file_format.extension}"

    def write(self, df: pd.DataFrame, source: str, table: str, run: RunContext) -> str:
        key = self.build_key(source, table, run)
        uri = self.storage.put(key, self.file_format.serialize(df))
        if self.write_mode == "overwrite_partition":
            replaced = [k for k in self.storage.list_keys(self.partition(source, table, run)) if k != key]
            for old_key in replaced:
                self.storage.delete(old_key)
            if replaced and getattr(self.storage, "dry_run", False):
                logger.info("[%s.%s] partition load_date=%s : %d fichier(s) d'un run précédent seraient remplacé(s) "
                            "(dry-run, rien n'est supprimé)", source, table, run.load_date, len(replaced))
            elif replaced:
                logger.info("[%s.%s] partition load_date=%s : %d fichier(s) d'un run précédent remplacé(s)",
                            source, table, run.load_date, len(replaced))
        return uri

    def report_key(self, run: RunContext) -> str:
        return f"{self.prefix}/_runs/load_date={run.load_date}/{run.run_id}.json"

    def write_report(self, report: RunReport) -> str:
        return self.storage.put(self.report_key(report.run), report.to_json())

    def read_report(self, run_id: str) -> dict:
        matches = [k for k in self.storage.list_keys(f"{self.prefix}/_runs/") if k.endswith(f"/{run_id}.json")]
        if not matches:
            raise FileNotFoundError(f"aucun manifeste pour le run {run_id} sous {self.prefix}/_runs/")
        return json.loads(self.storage.get(matches[0]))
