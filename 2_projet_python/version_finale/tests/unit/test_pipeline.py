import io
import json
import logging

import pandas as pd
import pytest

from conftest import FakeConnector
from fhvi_ingestion.pipeline import IngestionPipeline, PipelineAborted
from fhvi_ingestion.report import Status
from fhvi_ingestion.writers import DatasetWriter, ParquetFormat


@pytest.fixture
def source_data():
    return {
        "patients": pd.DataFrame({"IPP": ["IPP1", "IPP2"], "Sexe": ["F ", " M"]}),
        "sejours": pd.DataFrame({"ID_SEJOUR": [10, 11, 12]}),
    }


@pytest.fixture
def build_pipeline(memory_storage, source_data, run_context):
    created: list[FakeConnector] = []

    def _build(fail_fast: bool = False, broken_sources: tuple[str, ...] = ()):
        def fake_factory(source):
            if source.name in broken_sources:
                raise ConnectionError(f"{source.name} : connexion refusée")
            connector = FakeConnector(source, source_data)
            created.append(connector)
            return connector

        writer = DatasetWriter(memory_storage, ParquetFormat(), prefix="raw")
        return IngestionPipeline(writer, run_context, connector_factory=fake_factory, fail_fast=fail_fast)

    _build.created = created
    return _build


def read_written(memory_storage, table: str) -> pd.DataFrame:
    key = next(k for k in memory_storage.objects if f"/{table}/" in k)
    return pd.read_parquet(io.BytesIO(memory_storage.objects[key]))


def test_success_run(build_pipeline, make_source, memory_storage):
    report = build_pipeline().run([make_source("dpi_nord", tables=["patients", "sejours"])])
    assert report.status is Status.SUCCESS
    assert report.exit_code == 0
    assert [(r.table, r.rows) for r in report.results] == [("patients", 2), ("sejours", 3)]
    assert len(memory_storage.objects) == 2


def test_written_data_is_normalized_and_carries_metadata(build_pipeline, make_source, memory_storage):
    build_pipeline().run([make_source("dpi_nord", tables=["patients"])])
    written = read_written(memory_storage, "patients")
    assert written["sexe"].tolist() == ["F", "M"]
    assert set(written["_run_id"]) == {"20261109T020000Z-abcd1234"}
    assert set(written["_source_name"]) == {"dpi_nord"}


def test_each_connection_is_closed(build_pipeline, make_source):
    build_pipeline().run([make_source("a", tables=["patients"]), make_source("b", tables=["sejours"])])
    assert [c.closed for c in build_pipeline.created] == [1, 1]


def test_a_failing_table_does_not_stop_the_others(build_pipeline, make_source, memory_storage):
    report = build_pipeline().run([make_source("dpi_nord", tables=["absente", "patients"])])
    assert report.status is Status.PARTIAL
    assert report.exit_code == 1
    failed = report.failed[0]
    assert failed.table == "absente" and "indisponible" in failed.error
    assert len(memory_storage.objects) == 1


def test_an_unreachable_source_does_not_stop_the_others(build_pipeline, make_source):
    sources = [make_source("rdv_sud", tables=["patients", "sejours"]), make_source("pharmacie", tables=["sejours"])]
    report = build_pipeline(broken_sources=("rdv_sud",)).run(sources)
    assert [(r.source, r.status) for r in report.results] == [
        ("rdv_sud", Status.FAILED), ("rdv_sud", Status.FAILED), ("pharmacie", Status.SUCCESS)]


def test_all_tables_failing_gives_failed_status(build_pipeline, make_source):
    report = build_pipeline(broken_sources=("x",)).run([make_source("x")])
    assert report.status is Status.FAILED


def test_fail_fast_stops_at_first_error(build_pipeline, make_source, memory_storage):
    with pytest.raises(PipelineAborted):
        build_pipeline(fail_fast=True).run([make_source("a", tables=["absente", "patients"])])
    assert memory_storage.objects == {}


def test_fail_fast_keeps_a_report_with_the_tables_not_run(build_pipeline, make_source):
    # sans ça --rerun-failed ne saurait pas quoi reprendre après un arrêt --fail-fast
    with pytest.raises(PipelineAborted) as aborted:
        build_pipeline(fail_fast=True).run([make_source("a", tables=["absente", "patients"]),
                                            make_source("b", tables=["patients"])])
    report = aborted.value.report
    assert [(r.source, r.table) for r in report.results] == [("a", "absente"), ("a", "patients"), ("b", "patients")]
    assert all(r.status is Status.FAILED for r in report.results)
    assert report.results[1].error == "non lancée (arrêt --fail-fast)"


def test_logs_tell_the_story_of_the_run(build_pipeline, make_source, caplog):
    caplog.set_level(logging.INFO, logger="fhvi_ingestion")
    build_pipeline().run([make_source("dpi_nord", tables=["absente", "patients"])])

    messages = [(r.levelname, r.getMessage()) for r in caplog.records]
    assert any(lvl == "INFO" and "Début du run" in msg for lvl, msg in messages)
    assert any(lvl == "ERROR" and "[dpi_nord.absente] ÉCHEC" in msg for lvl, msg in messages)
    assert any(lvl == "INFO" and "[dpi_nord.patients] OK - 2 lignes" in msg for lvl, msg in messages)
    assert any(lvl == "WARNING" and "statut PARTIAL" in msg for lvl, msg in messages)


def test_empty_table_emits_a_warning(memory_storage, run_context, make_source, caplog):
    def factory(source):
        return FakeConnector(source, {"vide": pd.DataFrame({"a": []})})
    pipeline = IngestionPipeline(DatasetWriter(memory_storage, ParquetFormat()), run_context, factory)
    pipeline.run([make_source("s", tables=["vide"])])
    assert any(r.levelname == "WARNING" and "vide" in r.getMessage() for r in caplog.records)


def test_report_is_serializable(build_pipeline, make_source):
    report = build_pipeline().run([make_source("dpi_nord", tables=["patients"])])
    payload = json.loads(report.to_json())
    assert payload["run_id"] == "20261109T020000Z-abcd1234"
    assert payload["status"] == "SUCCESS"
    assert payload["rows_total"] == 2
    assert payload["results"][0]["status"] == "SUCCESS"
