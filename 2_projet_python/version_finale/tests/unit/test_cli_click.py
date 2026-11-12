import importlib.util
from pathlib import Path

import pytest

click_testing = pytest.importorskip("click.testing")
EXAMPLE = Path(__file__).resolve().parents[2] / "exemples" / "cli_click.py"


@pytest.fixture
def cli():
    spec = importlib.util.spec_from_file_location("cli_click", EXAMPLE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_click_exposes_the_replay_subcommands(cli):
    result = click_testing.CliRunner().invoke(cli.cli, ["--help"])
    assert result.exit_code == 0
    for command in ("run", "tables", "rerun", "list-sources"):
        assert command in result.output


def test_click_translates_options_into_the_same_arguments(cli, monkeypatch, tmp_path):
    config = tmp_path / "p.yaml"
    config.write_text("x: 1", encoding="utf-8")
    received = {}
    monkeypatch.setattr(cli, "run_app", lambda argv: received.setdefault("argv", argv) and 0)
    result = click_testing.CliRunner().invoke(
        cli.cli, ["tables", "fact_ouest.prestations", "-c", str(config), "-d", "2025-03-14", "--dry-run"])
    assert result.exit_code == 0
    assert received["argv"] == ["--config", str(config), "--log-level", "INFO", "--load-date", "2025-03-14",
                                "--dry-run", "--tables", "fact_ouest.prestations"]


def test_click_run_example_from_the_docstring_works(cli, monkeypatch, tmp_path):
    config = tmp_path / "p.yaml"
    config.write_text("x: 1", encoding="utf-8")
    received = {}
    monkeypatch.setattr(cli, "run_app", lambda argv: received.setdefault("argv", argv) and 0)
    result = click_testing.CliRunner().invoke(
        cli.cli, ["run", "-c", str(config), "-s", "dpi_nord", "-s", "fact_ouest", "--dry-run"])
    assert result.exit_code == 0
    assert received["argv"][-3:] == ["--sources", "dpi_nord", "fact_ouest"]
    assert "run -s dpi_nord -s fact_ouest" in cli.__doc__
