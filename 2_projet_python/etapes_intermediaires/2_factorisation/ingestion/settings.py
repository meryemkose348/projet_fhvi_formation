"""Paramètres de l'appli, tous lus dans les variables d'environnement

hôtes, ports, mots de passe, bucket... viennent du .env à la racine de 2_projet_python/.
plus aucun secret en dur dans le code
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

# usecwd=True : on cherche le .env en partant du dossier courant et en remontant (-> 2_projet_python/.env).
# sans ça find_dotenv part du dossier du fichier appelant, pas forcément celui d'où on lance
_ENV_FILE = find_dotenv(usecwd=True)
load_dotenv(_ENV_FILE)
_BASE_DIR = Path(_ENV_FILE).parent if _ENV_FILE else Path.cwd()


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Variable d'environnement manquante : {name} (voir .env.example)")
    return value


PG_URL = (
    f"postgresql+psycopg://{_require('PG_USER')}:{_require('PG_PASSWORD')}"
    f"@{_require('PG_HOST')}:{_require('PG_PORT')}/{_require('PG_DB')}"
)
MARIADB_URL = (
    f"mysql+pymysql://{_require('MARIADB_USER')}:{_require('MARIADB_PASSWORD')}"
    f"@{_require('MARIADB_HOST')}:{_require('MARIADB_PORT')}/{_require('MARIADB_DB')}"
)
MSSQL_URL = (
    f"mssql+pymssql://{_require('MSSQL_USER')}:{_require('MSSQL_PASSWORD')}"
    f"@{_require('MSSQL_HOST')}:{_require('MSSQL_PORT')}/{_require('MSSQL_DB')}"
)
DUCKDB_PATH = (_BASE_DIR / _require("DUCKDB_PATH")).resolve()

S3_ENDPOINT_URL = _require("S3_ENDPOINT_URL")
S3_ACCESS_KEY = _require("S3_ACCESS_KEY")
S3_SECRET_KEY = _require("S3_SECRET_KEY")
S3_BUCKET = _require("S3_BUCKET")
