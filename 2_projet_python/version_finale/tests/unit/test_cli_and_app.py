import json
import logging
import textwrap
from datetime import date

import pytest

from fhvi_ingestion.app import EXIT_CONFIG_ERROR, EXIT_OK, EXIT_TABLE_FAILURE, main
from fhvi_ingestion.cli import parse_args
from fhvi_ingestion.logging_setup import configure_logging


def test_default_values():
    args = parse_args([])
    assert args.config == "config/pipeline.yaml"
    assert args.load_date == date.today().isoformat()
    assert args.log_level == "INFO"
    assert args.dry_run is False and args.fail_fast is False


def test_log_level_is_case_insensitive():
    assert parse_args(["--log-level", "debug"]).log_level == "DEBUG"


def test_invalid_date_exits_with_code_2(capsys):
    with pytest.raises(SystemExit) as exc_info:
        parse_args(["--load-date", "2026-13-45"])
    assert exc_info.value.code == 2
    assert "date invalide" in capsys.readouterr().err


def test_invalid_config_returns_exit_code_2(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("destination: {type: ftp}\nsources: []\n", encoding="utf-8")
    assert main(["--config", str(bad)]) == EXIT_CONFIG_ERROR


def test_local_end_to_end_with_duckdb(tmp_path, duckdb_file):
    config = tmp_path / "local.yaml"
    config.write_text(textwrap.dedent(f"""
        destination: {{type: local, path: {tmp_path / 'out'}, format: csv}}
        sources:
          - name: pharmacie
            type: duckdb
            connection: {{path: {duckdb_file}}}
            tables: [{{name: produits}}]
    """), encoding="utf-8")

    assert main(["--config", str(config), "--load-date", "2026-11-09"]) == EXIT_OK

    written = list((tmp_path / "out/raw/pharmacie/produits/load_date=2026-11-09").glob("produits__*.csv"))
    assert len(written) == 1
    header, first_row = written[0].read_text(encoding="utf-8").splitlines()[:2]
    assert header.startswith("code_ucd,libelle,_run_id,_source_name")
    assert ",Paracétamol," in first_row
    assert list((tmp_path / "out/raw/_runs/load_date=2026-11-09").glob("*.json"))


def test_configure_logging_writes_run_id_in_log_file(tmp_path):
    log_file = tmp_path / "logs" / "run.log"
    configure_logging("INFO", run_id="RUN-42", log_file=log_file)
    logging.getLogger("fhvi_ingestion.test").info("bonjour")
    logging.getLogger("fhvi_ingestion.test").debug("invisible en INFO")
    for handler in logging.getLogger().handlers:
        handler.flush()
    content = log_file.read_text(encoding="utf-8")
    assert "| INFO     | run=RUN-42 | fhvi_ingestion.test | bonjour" in content
    assert "invisible" not in content
    configure_logging("WARNING")


def test_fail_fast_still_writes_the_manifest(tmp_path, duckdb_file):
    config = tmp_path / "local.yaml"
    config.write_text(textwrap.dedent(f"""
        destination: {{type: local, path: {tmp_path / 'out'}, format: csv}}
        sources:
          - name: pharmacie
            type: duckdb
            connection: {{path: {duckdb_file}}}
            tables: [{{name: absente}}, {{name: produits}}]
    """), encoding="utf-8")

    assert main(["--config", str(config), "--load-date", "2026-11-09", "--fail-fast"]) == EXIT_TABLE_FAILURE

    manifests = list((tmp_path / "out/raw/_runs/load_date=2026-11-09").glob("*.json"))
    assert len(manifests) == 1
    results = json.loads(manifests[0].read_text(encoding="utf-8"))["results"]
    assert [(r["table"], r["status"]) for r in results] == [("absente", "FAILED"), ("produits", "FAILED")]
