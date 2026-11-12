"""Colonnes techniques ajoutées à chaque ligne écrite.
les logs racontent l'exécution et finissent par disparaître ; les colonnes qu'on definit ici, elles, voyagent
avec la donnée et disent d'où vient chaque ligne. Préfixe « _ » réservé à ces colonnes pour les distinguer
"""
from __future__ import annotations

from datetime import datetime

import pandas as pd

from fhvi_ingestion.run_context import RunContext

TECHNICAL_COLUMNS = (
    "_run_id",
    "_source_name",
    "_source_table",
    "_load_date",
    "_extracted_at",
    "_load_timestamp",
)


def add_technical_columns(
    df: pd.DataFrame,
    run: RunContext,
    source_name: str,
    source_table: str,
    extracted_at: datetime,
    load_timestamp: datetime,
) -> pd.DataFrame:
    # si la source a déjà une colonne _run_id & co on refuse : sinon ça aurait écrsé une donnée métier en silence
    conflicts = [c for c in TECHNICAL_COLUMNS if c in df.columns]
    if conflicts:
        raise ValueError(f"colonnes techniques déjà présentes dans la source : {conflicts}")
    # assign renvoie une copie, le df d'origine n'est pas modifié
    return df.assign(
        _run_id=run.run_id,
        _source_name=source_name,
        _source_table=source_table,
        _load_date=pd.Timestamp(run.load_date).date(),
        _extracted_at=pd.Timestamp(extracted_at),
        _load_timestamp=pd.Timestamp(load_timestamp),
    )
