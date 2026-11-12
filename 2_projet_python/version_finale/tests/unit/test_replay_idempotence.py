import json
import textwrap
from dataclasses import replace
from unittest.mock import MagicMock

import duckdb
import pandas as pd
import pytest

from fhvi_ingestion.app import EXIT_CONFIG_ERROR, EXIT_OK, EXIT_TABLE_FAILURE, main
from fhvi_ingestion.config import ConfigError, DestinationConfig, PipelineConfig, TableConfig
from fhvi_ingestion.writers import CsvFormat, DatasetWriter, DryRunStorage, LocalStorage, S3Storage


@pytest.fixture
def df():
    return pd.DataFrame({"id": [1, 2]})


def test_overwrite_partition_keeps_a_single_file_per_partition(memory_storage, df, run_context):
    writer = DatasetWriter(memory_storage, CsvFormat())
    writer.write(df, "dpi_nord", "patients", run_context)
    rejeu = replace(run_context, run_id="20261110T020000Z-ffff0000")
    writer.write(df, "dpi_nord", "patients", rejeu)
    assert list(memory_storage.objects) == [
        "raw/dpi_nord/patients/load_date=2026-11-09/patients__20261110T020000Z-ffff0000.csv"]


def test_overwrite_partition_does_not_touch_other_dates_or_tables(memory_storage, df, run_context):
    writer = DatasetWriter(memory_storage, CsvFormat())
    writer.write(df, "dpi_nord", "patients", run_context)
    writer.write(df, "dpi_nord", "sejours", run_context)
    writer.write(df, "dpi_nord", "patients", replace(run_context, run_id="R2", load_date="2026-11-10"))
    assert len(memory_storage.objects) == 3


def test_append_mode_keeps_every_file(memory_storage, df, run_context):
    writer = DatasetWriter(memory_storage, CsvFormat(), write_mode="append")
    writer.write(df, "dpi_nord", "patients", run_context)
    writer.write(df, "dpi_nord", "patients", replace(run_context, run_id="R2"))
    assert len(memory_storage.objects) == 2


def test_unknown_write_mode_is_refused(memory_storage):
    with pytest.raises(ValueError, match="write_mode"):
        DatasetWriter(memory_storage, CsvFormat(), write_mode="upsert")


# l ordre compte : si le put plante, l'ancienne version est tjrs là, et le fichier du run courant
# (même nom que la clé qu on écrit) ne doit pas être supprimé
def test_new_file_is_written_before_old_ones_are_deleted(df, run_context):
    calls = []
    storage = MagicMock()
    storage.put.side_effect = lambda key, body: calls.append(("put", key)) or key
    storage.list_keys.return_value = ["raw/s/t/load_date=2026-11-09/t__OLD.csv",
                                      "raw/s/t/load_date=2026-11-09/t__20261109T020000Z-abcd1234.csv"]
    storage.delete.side_effect = lambda key: calls.append(("delete", key))
    DatasetWriter(storage, CsvFormat()).write(df, "s", "t", run_context)
    assert calls == [("put", "raw/s/t/load_date=2026-11-09/t__20261109T020000Z-abcd1234.csv"),
                     ("delete", "raw/s/t/load_date=2026-11-09/t__OLD.csv")]


def test_local_storage_lists_reads_and_deletes(tmp_path):
    storage = LocalStorage(tmp_path)
    storage.put("raw/a/x.csv", b"1")
    storage.put("raw/b/y.csv", b"2")
    assert storage.list_keys("raw/a/") == ["raw/a/x.csv"]
    assert storage.get("raw/b/y.csv") == b"2"
    storage.delete("raw/a/x.csv")
    assert storage.list_keys("raw/") == ["raw/b/y.csv"]
    with pytest.raises(FileNotFoundError):
        storage.get("raw/absent.csv")


def test_s3_storage_lists_with_pagination_and_deletes():
    client = MagicMock()
    client.get_paginator.return_value.paginate.return_value = [
        {"Contents": [{"Key": "raw/b"}, {"Key": "raw/a"}]}, {"Contents": [{"Key": "raw/c"}]}, {}]
    storage = S3Storage("fhvi-landing", client)
    assert storage.list_keys("raw/") == ["raw/a", "raw/b", "raw/c"]
    storage.delete("raw/a")
    client.delete_object.assert_called_once_with(Bucket="fhvi-landing", Key="raw/a")


def test_dry_run_reads_through_but_never_writes_or_deletes(memory_storage):
    memory_storage.put("raw/_runs/x.json", b"{}")
    dry = DryRunStorage(inner=memory_storage)
    assert dry.get("raw/_runs/x.json") == b"{}"
    dry.put("raw/new.csv", b"1")
    dry.delete("raw/_runs/x.json")
    assert list(memory_storage.objects) == ["raw/_runs/x.json"]


def test_load_date_placeholder_is_rendered():
    table = TableConfig("fact.Prestations", "prestations",
                        query="SELECT * FROM fact.Prestations WHERE CAST(DateMaj AS DATE) = '{load_date}'")
    assert table.sql_for("2025-03-14").endswith("= '2025-03-14'")
    assert TableConfig("patients", "patients").sql_for("2025-03-14") == "SELECT * FROM patients"


def test_select_tables_by_name_or_target_including_disabled_sources(make_source):
    config = PipelineConfig(DestinationConfig(type="local", path="."), [
        replace(make_source("fact_ouest", tables=["fact.Prestations"]), enabled=False),
        make_source("dpi_nord", tables=["patients", "sejours"])])
    selected = config.select_tables(["fact_ouest.fact.prestations", "dpi_nord.sejours"])
    assert [(s.name, [t.name for t in s.tables]) for s in selected] == [
        ("fact_ouest", ["fact.Prestations"]), ("dpi_nord", ["sejours"])]


def test_select_unknown_table_is_refused(make_source):
    config = PipelineConfig(DestinationConfig(type="local", path="."), [make_source("dpi_nord")])
    with pytest.raises(ConfigError, match="dpi_nord.inconnue"):
        config.select_tables(["dpi_nord.inconnue"])


@pytest.fixture
def local_setup(tmp_path):
    db = tmp_path / "pharma.duckdb"
    with duckdb.connect(str(db)) as con:
        con.execute("CREATE TABLE produits (CodeUCD VARCHAR)")
        con.execute("INSERT INTO produits VALUES ('001'), ('002')")
    config = tmp_path / "local.yaml"
    config.write_text(textwrap.dedent(f"""
        destination: {{type: local, path: {tmp_path / 'out'}, format: csv}}
        sources:
          - name: pharmacie
            type: duckdb
            connection: {{path: {db}}}
            tables: [{{name: produits}}, {{name: stocks}}]
    """), encoding="utf-8")
    return tmp_path, db, config


def _manifests(out):
    return sorted((out / "raw/_runs").rglob("*.json"))


def test_running_twice_the_same_date_is_idempotent(local_setup):
    tmp_path, _, config = local_setup
    for _ in range(2):
        main(["--config", str(config), "--load-date", "2026-11-09", "--tables", "pharmacie.produits"])
    files = list((tmp_path / "out/raw/pharmacie/produits/load_date=2026-11-09").glob("*.csv"))
    assert len(files) == 1
    assert len(_manifests(tmp_path / "out")) == 2


def test_rerun_failed_replays_only_failed_tables_at_the_original_date(local_setup):
    tmp_path, db, config = local_setup
    assert main(["--config", str(config), "--load-date", "2026-11-01"]) == EXIT_TABLE_FAILURE
    first = json.loads(_manifests(tmp_path / "out")[0].read_text(encoding="utf-8"))
    assert [r["table"] for r in first["results"] if r["status"] == "FAILED"] == ["stocks"]

    with duckdb.connect(str(db)) as con:
        con.execute("CREATE TABLE stocks (CodeUCD VARCHAR, Quantite INTEGER)")
    assert main(["--config", str(config), "--rerun-failed", first["run_id"]]) == EXIT_OK

    replay = next(json.loads(m.read_text(encoding="utf-8")) for m in _manifests(tmp_path / "out")
                  if json.loads(m.read_text(encoding="utf-8"))["run_id"] != first["run_id"])
    assert replay["replay_of"] == first["run_id"]
    assert replay["load_date"] == "2026-11-01"
    assert [r["table"] for r in replay["results"]] == ["stocks"]


def test_rerun_of_an_unknown_run_is_refused(local_setup):
    _, _, config = local_setup
    assert main(["--config", str(config), "--rerun-failed", "20000101T000000Z-inconnu"]) == EXIT_CONFIG_ERROR


def test_rerun_with_nothing_failed_does_nothing(local_setup):
    tmp_path, _, config = local_setup
    main(["--config", str(config), "--tables", "pharmacie.produits"])
    run_id = json.loads(_manifests(tmp_path / "out")[0].read_text(encoding="utf-8"))["run_id"]
    assert main(["--config", str(config), "--rerun-failed", run_id]) == EXIT_OK
    assert len(_manifests(tmp_path / "out")) == 1


def test_sources_tables_and_rerun_are_mutually_exclusive(capsys):
    from fhvi_ingestion.cli import parse_args
    with pytest.raises(SystemExit):
        parse_args(["--sources", "dpi_nord", "--tables", "dpi_nord.patients"])
    assert "not allowed with" in capsys.readouterr().err
