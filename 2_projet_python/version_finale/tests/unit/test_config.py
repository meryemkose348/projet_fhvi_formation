import textwrap

import pytest

from fhvi_ingestion.config import ConfigError, interpolate_env, load_config

SOURCE_TYPES = {"postgres": ("host", "port", "database", "user", "password"), "duckdb": ("path",)}
DEST_TYPES = {"s3": ("bucket",), "local": ("path",)}
FORMATS = {"parquet", "csv"}


@pytest.fixture
def write_yaml(tmp_path):
    def _write(content: str):
        path = tmp_path / "pipeline.yaml"
        path.write_text(textwrap.dedent(content), encoding="utf-8")
        return path
    return _write


def load(path):
    return load_config(path, SOURCE_TYPES, DEST_TYPES, FORMATS)


VALID = """
    destination: {type: local, path: ./out, format: csv}
    sources:
      - name: pharmacie
        type: duckdb
        connection: {path: /tmp/pharmacie.duckdb}
        tables:
          - name: dispensations
          - name: PRODUITS
            target: produits
            query: SELECT CodeUCD FROM PRODUITS
      - name: dpi
        type: postgres
        enabled: false
        connection: {host: h, port: 5432, database: d, user: u, password: p}
        tables: [{name: patients}]
"""


def test_valid_config_is_loaded(write_yaml):
    config = load(write_yaml(VALID))
    assert config.destination.format == "csv"
    assert config.source_names() == ["pharmacie", "dpi"]
    produits = config.sources[0].tables[1]
    assert produits.target == "produits"
    assert produits.sql == "SELECT CodeUCD FROM PRODUITS"
    assert config.sources[0].tables[0].sql == "SELECT * FROM dispensations"


def test_select_returns_only_enabled_sources_by_default(write_yaml):
    config = load(write_yaml(VALID))
    assert [s.name for s in config.select()] == ["pharmacie"]


def test_select_can_force_a_disabled_source(write_yaml):
    config = load(write_yaml(VALID))
    assert [s.name for s in config.select(["dpi"])] == ["dpi"]


def test_select_unknown_source_raises(write_yaml):
    config = load(write_yaml(VALID))
    with pytest.raises(ConfigError, match="inconnue"):
        config.select(["oracle_sud"])


def test_missing_file_raises(tmp_path):
    with pytest.raises(ConfigError, match="introuvable"):
        load(tmp_path / "absent.yaml")


def test_malformed_yaml_raises(write_yaml):
    with pytest.raises(ConfigError, match="mal formé"):
        load(write_yaml("sources: [unclosed"))


def test_all_errors_are_reported_at_once(write_yaml):
    path = write_yaml("""
        destination: {type: ftp, format: xlsx}
        sources:
          - name: a
            type: oracle
            tables: []
          - name: a
            type: postgres
            connection: {host: h}
            tables: [{name: t}]
    """)
    with pytest.raises(ConfigError) as exc_info:
        load(path)
    message = str(exc_info.value)
    for expected in ["destination.type 'ftp'", "format 'xlsx'", "type 'oracle'",
                     "doublon", "connection.password", "au moins une table"]:
        assert expected in message


def test_interpolate_env_replaces_variables(monkeypatch):
    monkeypatch.setenv("PG_HOST", "db.fhvi.local")
    errors: list[str] = []
    result = interpolate_env({"host": "${PG_HOST}", "port": 5432}, errors)
    assert result == {"host": "db.fhvi.local", "port": 5432}
    assert errors == []


def test_interpolate_env_reports_missing_variable(monkeypatch):
    monkeypatch.delenv("VARIABLE_ABSENTE", raising=False)
    errors: list[str] = []
    interpolate_env(["${VARIABLE_ABSENTE}"], errors)
    assert errors == ["variable d'environnement absente : ${VARIABLE_ABSENTE}"]


def test_unknown_destination_key_is_a_config_error(write_yaml):
    path = write_yaml(VALID.replace("format: csv}", "format: csv, endpoint_ur: http://x}"))
    with pytest.raises(ConfigError, match=r"clé\(s\) inconnue\(s\) \['endpoint_ur'\]"):
        load(path)


def test_backslash_in_double_quotes_is_caught(write_yaml):
    # "SRV-FACT01\PROD" entre guillemets doubles : YAML en fait SRV-FACT01 + U+2029 + ROD
    path = write_yaml(VALID.replace("{host: h,", '{host: "SRV-FACT01\\PROD",'))
    with pytest.raises(ConfigError, match="caractère invisible"):
        load(path)
