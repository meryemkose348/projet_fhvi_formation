"""Connecteurs de sources """
# charger duckdb_adapter et sql exécute les @register_connector,
# c est ça qui remplit le register factory. nouveau type de source = nouveau module, à importer ici
from ingestion.connectors import duckdb_adapter, sql  # noqa: F401  (enregistrement)
from ingestion.connectors.base import BaseConnector
from ingestion.connectors.factory import (
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
