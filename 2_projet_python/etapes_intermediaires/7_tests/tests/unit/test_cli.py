from datetime import date

import pytest

from ingestion.cli import parse_args


def test_default_values():
    args = parse_args([])
    assert args.config == "config/pipeline.yaml"
    assert args.sources is None
    assert args.load_date == date.today().isoformat()
    assert args.dry_run is False


def test_sources_and_flags():
    args = parse_args(["-s", "dpi_nord", "rdv_sud", "--dry-run", "-d", "2026-11-01"])
    assert args.sources == ["dpi_nord", "rdv_sud"]
    assert args.dry_run is True
    assert args.load_date == "2026-11-01"


def test_invalid_date_exits_with_code_2(capsys):
    with pytest.raises(SystemExit) as exc_info:
        parse_args(["--load-date", "2026-13-45"])
    assert exc_info.value.code == 2
    assert "date invalide" in capsys.readouterr().err
