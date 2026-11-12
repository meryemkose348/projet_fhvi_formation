from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from fhvi_ingestion.config import SourceConfig, TableConfig
from fhvi_ingestion.connectors import (
    BaseConnector,
    UnknownConnectorError,
    available_connectors,
    create_connector,
    register_connector,
)
from fhvi_ingestion.connectors.duckdb_adapter import DuckDBConnector
from fhvi_ingestion.connectors.factory import _REGISTRY
from fhvi_ingestion.connectors.sql import MariaDBConnector, PostgresConnector, SqlServerConnector

PG_CONNECTION = {"host": "localhost", "port": "5432", "database": "dpi",
                 "user": "lecteur", "password": "p@ss:w/rd"}


@pytest.mark.parametrize(("type_", "expected_class"), [
    ("postgres", PostgresConnector),
    ("mariadb", MariaDBConnector),
    ("sqlserver", SqlServerConnector),
    ("duckdb", DuckDBConnector),
])
def test_factory_creates_the_right_connector(make_source, type_, expected_class):
    connector = create_connector(make_source(type_=type_))
    assert isinstance(connector, expected_class)


def test_factory_rejects_unknown_type(make_source):
    with pytest.raises(UnknownConnectorError, match="oracle"):
        create_connector(make_source(type_="oracle"))


def test_available_connectors_exposes_required_keys():
    assert available_connectors()["duckdb"] == ("path",)
    assert "password" in available_connectors()["postgres"]


def test_registering_a_new_connector_needs_no_factory_change(make_source):
    @register_connector("api_test")
    class ApiConnector(BaseConnector):
        def _open(self): ...
        def _read(self, query): return pd.DataFrame({"a": [1]})
        def _close(self): ...

    try:
        connector = create_connector(make_source(type_="api_test"))
        assert isinstance(connector, ApiConnector)
    finally:
        _REGISTRY.pop("api_test")


def test_registering_twice_the_same_type_fails():
    with pytest.raises(ValueError, match="déjà enregistré"):
        register_connector("postgres")(PostgresConnector)


def test_base_connector_cannot_be_instantiated(make_source):
    with pytest.raises(TypeError):
        BaseConnector(make_source())


def test_extract_rejects_a_read_that_does_not_return_a_dataframe(make_source):
    class BrokenConnector(BaseConnector):
        def _open(self): ...
        def _read(self, query): return [1, 2, 3]
        def _close(self): ...

    with pytest.raises(TypeError, match="DataFrame"):
        BrokenConnector(make_source()).extract(TableConfig("t", "t"))


def test_duckdb_connector_reads_a_table(duckdb_file):
    source = SourceConfig("pharmacie", "duckdb", {"path": str(duckdb_file)},
                          [TableConfig("produits", "produits")])
    with create_connector(source) as connector:
        df = connector.extract(source.tables[0])
    assert len(df) == 2
    assert list(df.columns) == ["CodeUCD", "Libelle"]


def test_duckdb_connector_supports_custom_query(duckdb_file):
    source = SourceConfig("pharmacie", "duckdb", {"path": str(duckdb_file)}, [])
    table = TableConfig("produits", "produits", query="SELECT CodeUCD FROM produits WHERE CodeUCD = '002'")
    with create_connector(source) as connector:
        df = connector.extract(table)
    assert df["CodeUCD"].tolist() == ["002"]


def test_context_manager_closes_the_connection(duckdb_file):
    source = SourceConfig("pharmacie", "duckdb", {"path": str(duckdb_file)}, [])
    with create_connector(source) as connector:
        assert connector._is_open
    assert not connector._is_open


# côté SQL on mocke create_engine / read_sql, aucune vraie base derrière
def test_sql_url_escapes_special_characters_in_password():
    connector = PostgresConnector(SourceConfig("dpi", "postgres", PG_CONNECTION, []))
    url = connector._build_url()
    assert url.drivername == "postgresql+psycopg"
    assert url.password == "p@ss:w/rd"
    assert "p%40ss%3Aw%2Frd" in url.render_as_string(hide_password=False)


@patch("fhvi_ingestion.connectors.sql.pd.read_sql")
@patch("fhvi_ingestion.connectors.sql.create_engine")
def test_sql_connector_uses_sqlalchemy_without_real_database(mock_create_engine, mock_read_sql):
    mock_read_sql.return_value = pd.DataFrame({"id": [1, 2]})
    source = SourceConfig("dpi", "postgres", PG_CONNECTION, [TableConfig("patients", "patients")])

    with PostgresConnector(source) as connector:
        df = connector.extract(source.tables[0])

    assert len(df) == 2
    mock_create_engine.assert_called_once()
    assert mock_create_engine.call_args.kwargs["pool_pre_ping"] is True
    sent_query = mock_read_sql.call_args.args[0]
    assert str(sent_query) == "SELECT * FROM patients"
    mock_create_engine.return_value.dispose.assert_called_once()


def test_sql_connector_closes_engine_even_if_read_fails():
    source = SourceConfig("dpi", "postgres", PG_CONNECTION, [TableConfig("patients", "patients")])
    with patch("fhvi_ingestion.connectors.sql.create_engine") as mock_create_engine:
        engine = MagicMock()
        engine.connect.side_effect = ConnectionError("base indisponible")
        mock_create_engine.return_value = engine
        with pytest.raises(ConnectionError):
            with PostgresConnector(source) as connector:
                connector.extract(source.tables[0])
    engine.dispose.assert_called_once()


# sql server : pymssql pr la formation, pyodbc + auth Windows sur les serveurs FHVI
def test_sqlserver_training_mode_uses_pymssql():
    source = SourceConfig("fact_ouest", "sqlserver", {**PG_CONNECTION, "database": "FACTURATION_OUEST"}, [])
    url = SqlServerConnector(source)._build_url()
    assert url.drivername == "mssql+pymssql"
    assert url.database == "FACTURATION_OUEST"


def test_sqlserver_windows_authentication_like_fhvi_servers():
    connection = {"driver": "pyodbc", "host": r"SRV-DWH01\SQL2019", "database": "DWH",
                  "trusted_connection": True, "trust_server_certificate": True}
    url = SqlServerConnector(SourceConfig("dwh", "sqlserver", connection, []))._build_url()
    assert url.drivername == "mssql+pyodbc"
    assert url.username is None and url.password is None
    assert url.host == r"SRV-DWH01\SQL2019"
    assert url.query["Trusted_Connection"] == "yes"
    assert url.query["driver"] == "ODBC Driver 18 for SQL Server"


def test_sqlserver_pymssql_mode_requires_credentials():
    source = SourceConfig("fact_ouest", "sqlserver", {"host": "localhost", "database": "X"}, [])
    with pytest.raises(ValueError, match="clés manquantes"):
        SqlServerConnector(source)._build_url()


def test_sqlserver_only_requires_host_and_database_in_yaml():
    assert available_connectors()["sqlserver"] == ("host", "database")
