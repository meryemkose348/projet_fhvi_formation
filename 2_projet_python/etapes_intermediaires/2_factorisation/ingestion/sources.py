"""Les sources à ingérer, ce qui change d'une source à l'autre (type, connexion, tables) devient de la donnée,
le traitement commun reste du code (extract / transform / load)
Suite logique : sortir cette liste du code -> yml
"""
from __future__ import annotations

from ingestion import settings

SOURCES: list[dict] = [
    {"name": "dpi_nord", "kind": "sql", "location": settings.PG_URL,
     "tables": ["patients", "sejours"]},
    {"name": "rdv_sud", "kind": "sql", "location": settings.MARIADB_URL,
     "tables": ["RENDEZ_VOUS"]},
    {"name": "fact_ouest", "kind": "sql", "location": settings.MSSQL_URL,
     "tables": ["fact.Prestations"]},
    {"name": "pharmacie", "kind": "duckdb", "location": settings.DUCKDB_PATH,
     "tables": ["dispensations"]},
]
