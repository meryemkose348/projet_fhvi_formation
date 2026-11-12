"""Extraction des tables sources : c'est rangé dans son module, mais encore dupliqué : une fct par table, chacune avec sa connexion
et son nettoyage. C'est voulu, maintenant que c'est rangé la duplication saute aux yeux (cf module 3)
"""
from __future__ import annotations

import duckdb
import pandas as pd
from sqlalchemy import create_engine

from ingestion import settings


def extract_patients() -> pd.DataFrame:
    engine = create_engine(settings.PG_URL)
    df = pd.read_sql("SELECT * FROM patients", engine)
    df.columns = [c.lower() for c in df.columns]
    for c in df.columns:
        if df[c].dtype == object:
            df[c] = df[c].str.strip()
    return df


def extract_sejours() -> pd.DataFrame:
    engine = create_engine(settings.PG_URL)
    df = pd.read_sql("SELECT * FROM sejours", engine)
    df.columns = [c.lower() for c in df.columns]
    for c in df.columns:
        if df[c].dtype == object:
            df[c] = df[c].str.strip()
    return df


def extract_rendez_vous() -> pd.DataFrame:
    engine = create_engine(settings.MARIADB_URL)
    df = pd.read_sql("SELECT * FROM RENDEZ_VOUS", engine)
    df.columns = [c.lower() for c in df.columns]
    for c in df.columns:
        if df[c].dtype == object:
            df[c] = df[c].str.strip()
    return df


def extract_prestations() -> pd.DataFrame:
    engine = create_engine(settings.MSSQL_URL)
    df = pd.read_sql("SELECT * FROM fact.Prestations", engine)   # "fact" = le schéma côté SQL Server
    df.columns = [c.lower() for c in df.columns]
    for c in df.columns:
        if df[c].dtype == object:
            df[c] = df[c].str.strip()
    return df


def extract_dispensations() -> pd.DataFrame:
    con = duckdb.connect(str(settings.DUCKDB_PATH), read_only=True)
    df = con.execute("SELECT * FROM dispensations").df()
    con.close()
    df.columns = [c.lower() for c in df.columns]
    # FIXME pas de strip() ici alors que les 4 autres le font... avec du copier-coller
    # ce genre d'oubli passe inaperçu
    return df
