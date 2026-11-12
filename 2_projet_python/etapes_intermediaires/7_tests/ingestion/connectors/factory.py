"""factory + registre : créer le bon connecteur sans if/elif
"""
from __future__ import annotations

from collections.abc import Callable

from ingestion.config import SourceConfig
from ingestion.connectors.base import BaseConnector

# type de source -> classe. rempli par les décorateurs au moment de l'import
_REGISTRY: dict[str, type[BaseConnector]] = {}


class UnknownConnectorError(ValueError):
    """connectuer inconnu"""


# décorateur de classe : @register_connector("<type_db>") au-dessus de la classe et c est tout
def register_connector(type_name: str) -> Callable[[type[BaseConnector]], type[BaseConnector]]:
    def decorator(cls: type[BaseConnector]) -> type[BaseConnector]:
        if type_name in _REGISTRY:
            raise ValueError(f"Un connecteur '{type_name}' est déjà enregistré")
        cls.type_name = type_name
        _REGISTRY[type_name] = cls
        return cls
    return decorator


def create_connector(source: SourceConfig) -> BaseConnector:
    try:
        connector_class = _REGISTRY[source.type]
    except KeyError:
        raise UnknownConnectorError(
            f"Type de source '{source.type}' inconnu. Disponibles : {sorted(_REGISTRY)}"
        ) from None
    return connector_class(source)


def available_connectors() -> dict[str, tuple[str, ...]]:
    return {name: cls.required_keys for name, cls in _REGISTRY.items()}
