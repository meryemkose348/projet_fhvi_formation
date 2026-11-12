import io
from unittest.mock import MagicMock

import pandas as pd
import pytest

from fhvi_ingestion.config import DestinationConfig
from fhvi_ingestion.writers import (
    CsvFormat,
    DatasetWriter,
    DryRunStorage,
    LocalStorage,
    ParquetFormat,
    S3Storage,
    build_storage,
    get_format,
)


@pytest.fixture
def df():
    return pd.DataFrame({"id": [1, 2], "service": ["Urgences", "Pédiatrie"]})


def test_parquet_roundtrip_preserves_data(df):
    body = ParquetFormat().serialize(df)
    pd.testing.assert_frame_equal(pd.read_parquet(io.BytesIO(body)), df)


def test_csv_format_is_utf8_without_index(df):
    body = CsvFormat().serialize(df).decode("utf-8")
    assert body.splitlines() == ["id,service", "1,Urgences", "2,Pédiatrie"]


def test_get_format_rejects_unknown_format():
    with pytest.raises(ValueError, match="xlsx"):
        get_format("xlsx")


def test_local_storage_writes_file(tmp_path):
    uri = LocalStorage(tmp_path).put("raw/a/b.csv", b"x")
    assert (tmp_path / "raw/a/b.csv").read_bytes() == b"x"
    assert uri.endswith("raw/a/b.csv")


def test_s3_storage_calls_put_object_with_a_mocked_client():
    client = MagicMock()
    uri = S3Storage("fhvi-landing", client).put("raw/k.parquet", b"data")
    client.put_object.assert_called_once_with(Bucket="fhvi-landing", Key="raw/k.parquet", Body=b"data")
    assert uri == "s3://fhvi-landing/raw/k.parquet"


def test_dry_run_storage_writes_nothing(tmp_path):
    uri = DryRunStorage().put("raw/k.parquet", b"1234")
    assert "dry-run" in uri and "4 octets" in uri
    assert list(tmp_path.iterdir()) == []


def test_build_storage_selects_strategy_from_config(tmp_path):
    assert isinstance(build_storage(DestinationConfig(type="local", path=str(tmp_path))), LocalStorage)
    assert isinstance(build_storage(DestinationConfig(type="s3", bucket="b"), dry_run=True), DryRunStorage)


def test_dataset_writer_builds_a_partitioned_and_traceable_key(memory_storage, df, run_context):
    writer = DatasetWriter(memory_storage, CsvFormat(), prefix="raw")
    uri = writer.write(df, "dpi_nord", "sejours", run_context)
    key = "raw/dpi_nord/sejours/load_date=2026-11-09/sejours__20261109T020000Z-abcd1234.csv"
    assert uri == f"memory://{key}"
    assert memory_storage.objects[key].startswith(b"id,service")


def test_dataset_writer_writes_the_run_report(memory_storage, run_context):
    from fhvi_ingestion.report import RunReport
    report = RunReport(run=run_context)
    report.finish()
    DatasetWriter(memory_storage, CsvFormat(), prefix="raw").write_report(report)
    key = "raw/_runs/load_date=2026-11-09/20261109T020000Z-abcd1234.json"
    assert b'"status": "SUCCESS"' in memory_storage.objects[key]


def test_dry_run_does_not_delete_and_says_so(memory_storage, df, run_context, caplog):
    old_key = "raw/dpi_nord/sejours/load_date=2026-11-09/sejours__ancien-run.csv"
    memory_storage.objects[old_key] = b"old"
    writer = DatasetWriter(DryRunStorage(inner=memory_storage), CsvFormat(), prefix="raw")
    with caplog.at_level("INFO", logger="fhvi_ingestion"):
        writer.write(df, "dpi_nord", "sejours", run_context)
    assert old_key in memory_storage.objects
    assert "seraient remplacé(s)" in caplog.text and "rien n'est supprimé" in caplog.text
