"""config du logging, faite une seule fois ici. Les modules se contentent de logging.getLogger(__name__)"""
from __future__ import annotations

import logging
from pathlib import Path

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | run=%(run_id)s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class RunIdFilter(logging.Filter):
    def __init__(self, run_id: str) -> None:
        super().__init__()
        self.run_id = run_id

    def filter(self, record: logging.LogRecord) -> bool:
        record.run_id = self.run_id
        return True


def configure_logging(level: str = "INFO", run_id: str = "-", log_file: str | Path | None = None) -> None:
    root = logging.getLogger()
    root.setLevel(level.upper())
    # on vide les handlers existants : appel répété (tests) sans logs en double
    for handler in list(root.handlers):
        root.removeHandler(handler)
        handler.close()

    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))
    for handler in handlers:
        handler.setFormatter(formatter)
        # filtre posé sur le handler et pas sur le logger racine : un filtre de logger ne voit pas
        # les records qui remontent des loggers enfants -> %(run_id)s planterait le formatage
        handler.addFilter(RunIdFilter(run_id))
        root.addHandler(handler)

    # boto & co inondent la console en DEBUG
    for noisy in ("botocore", "boto3", "urllib3", "s3transfer"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
