""" test du pipeline complet
"""
import io

import pandas as pd
import pytest
from conftest import FakeConnector

from ingestion.pipeline import IngestionPipeline
from ingestion.writers import DatasetWriter, ParquetFormat


@pytest.fixture
def source_data():
    return {
        "patients": pd.DataFrame({"IPP": ["IPP1", "IPP2"], "Sexe": ["F ", " M"]}),
        "sejours": pd.DataFrame({"ID_SEJOUR": [10, 11, 12]}),
    }


@pytest.fixture
def pipeline_and_connectors(memory_storage, source_data):
    created: list[FakeConnector] = []

    def fake_factory(source):
        connector = FakeConnector(source, source_data)
        created.append(connector)
        return connector

    writer = DatasetWriter(memory_storage, ParquetFormat(), prefix="raw")
    pipeline = IngestionPipeline(writer, load_date="2026-11-09", connector_factory=fake_factory)
    return pipeline, created


def test_pipeline_ingests_every_table(pipeline_and_connectors, make_source, memory_storage):
    pipeline, _ = pipeline_and_connectors
    results = pipeline.run([make_source("dpi_nord", tables=["patients", "sejours"])])

    assert [(r.table, r.rows) for r in results] == [("patients", 2), ("sejours", 3)]
    assert sorted(memory_storage.objects) == [
        "raw/dpi_nord/patients/2026-11-09/patients.parquet",
        "raw/dpi_nord/sejours/2026-11-09/sejours.parquet",
    ]


def test_pipeline_writes_normalized_data(pipeline_and_connectors, make_source, memory_storage):
    pipeline, _ = pipeline_and_connectors
    pipeline.run([make_source("dpi_nord", tables=["patients"])])

    body = memory_storage.objects["raw/dpi_nord/patients/2026-11-09/patients.parquet"]
    written = pd.read_parquet(io.BytesIO(body))
    assert list(written.columns) == ["ipp", "sexe"]
    assert written["sexe"].tolist() == ["F", "M"]


def test_pipeline_opens_one_connection_per_source_and_closes_it(pipeline_and_connectors, make_source):
    pipeline, created = pipeline_and_connectors
    pipeline.run([make_source("a", tables=["patients", "sejours"]), make_source("b", tables=["sejours"])])

    assert len(created) == 2
    assert all(c.opened == 1 and c.closed == 1 for c in created)


def test_connection_is_closed_even_when_a_table_fails(pipeline_and_connectors, make_source):
    pipeline, created = pipeline_and_connectors
    with pytest.raises(RuntimeError, match="indisponible"):
        pipeline.run([make_source("a", tables=["table_absente"])])
    assert created[0].closed == 1
