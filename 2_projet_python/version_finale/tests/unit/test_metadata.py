import re
from datetime import UTC, datetime

import pandas as pd
import pytest

from fhvi_ingestion.metadata import TECHNICAL_COLUMNS, add_technical_columns
from fhvi_ingestion.run_context import RunContext, new_run_id

EXTRACTED = datetime(2026, 11, 9, 2, 0, 1, tzinfo=UTC)
LOADED = datetime(2026, 11, 9, 2, 0, 2, tzinfo=UTC)


def test_run_id_is_sortable_and_unique():
    now = datetime(2026, 11, 9, 14, 30, 12, tzinfo=UTC)
    first, second = new_run_id(now), new_run_id(now)
    assert re.fullmatch(r"20261109T143012Z-[0-9a-f]{8}", first)
    assert first != second


def test_run_context_create_sets_start_time():
    run = RunContext.create("2026-11-01")
    assert run.load_date == "2026-11-01"
    assert run.run_id.startswith(f"{run.started_at:%Y%m%dT%H%M%SZ}")


def test_all_technical_columns_are_added(run_context):
    df = pd.DataFrame({"ipp": ["IPP1", "IPP2"]})
    result = add_technical_columns(df, run_context, "dpi_nord", "patients", EXTRACTED, LOADED)
    assert list(result.columns) == ["ipp", *TECHNICAL_COLUMNS]
    row = result.iloc[0]
    assert row["_run_id"] == "20261109T020000Z-abcd1234"
    assert row["_source_name"] == "dpi_nord"
    assert row["_source_table"] == "patients"
    assert str(row["_load_date"]) == "2026-11-09"
    assert row["_extracted_at"] == pd.Timestamp(EXTRACTED)
    assert row["_load_timestamp"] == pd.Timestamp(LOADED)


def test_business_data_is_untouched(run_context):
    df = pd.DataFrame({"ipp": ["IPP1"]})
    add_technical_columns(df, run_context, "s", "t", EXTRACTED, LOADED)
    assert list(df.columns) == ["ipp"]


def test_conflict_with_existing_column_is_refused(run_context):
    df = pd.DataFrame({"_run_id": ["déjà là"]})
    with pytest.raises(ValueError, match="_run_id"):
        add_technical_columns(df, run_context, "s", "t", EXTRACTED, LOADED)
