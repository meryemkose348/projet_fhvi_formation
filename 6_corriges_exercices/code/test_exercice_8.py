""" correction de l'exercice 8 : tests complémentaires"""
import io
import json

import pandas as pd
import pytest

from fhvi_ingestion.cli import parse_args
from fhvi_ingestion.transform import to_snake_case
from fhvi_ingestion.writers import FORMATS, get_format


@pytest.mark.parametrize("value", ["2026-02-30", "09/11/2026", "hier", ""])
def test_invalid_dates_are_refused(value):
    with pytest.raises(SystemExit):
        parse_args(["--load-date", value])


def test_jsonl_format_writes_one_json_object_per_line():
    df = pd.DataFrame({"id": [1, 2], "service": ["Urgences", "Pédiatrie"],
                       "date": pd.to_datetime(["2026-11-09", "2026-11-10"])})
    lines = get_format("jsonl").serialize(df).decode("utf-8").splitlines()
    assert len(lines) == 2
    first = json.loads(lines[0])
    assert first["service"] == "Urgences" and first["date"].startswith("2026-11-09")


def test_jsonl_is_registered_and_accepted_by_validation():
    assert "jsonl" in FORMATS


def test_known_limit_of_to_snake_case_with_acronyms():
    assert to_snake_case("HTTPResponse") == "httpresponse"
    assert to_snake_case("IDPatient") == "idpatient"


def test_parquet_keeps_types_but_csv_does_not():
    df = pd.DataFrame({"n": [1, 2]})
    from_parquet = pd.read_parquet(io.BytesIO(get_format("parquet").serialize(df)))
    assert from_parquet["n"].dtype == df["n"].dtype
