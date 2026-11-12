from fhvi_ingestion.connectors import duckdb_adapter, sql  # noqa: F401  (enregistrement)
from fhvi_ingestion.connectors.base import BaseConnector
from fhvi_ingestion.connectors.factory import (
    UnknownConnectorError,
    available_connectors,
    create_connector,
    register_connector,
)

__all__ = [
    "BaseConnector",
    "UnknownConnectorError",
    "available_connectors",
    "create_connector",
    "register_connector",
]
