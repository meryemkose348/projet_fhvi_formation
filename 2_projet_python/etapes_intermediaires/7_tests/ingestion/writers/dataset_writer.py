from __future__ import annotations

import pandas as pd

from ingestion.writers.formats import FileFormat
from ingestion.writers.storage import Storage


class DatasetWriter:
    def __init__(self, storage: Storage, file_format: FileFormat, prefix: str = "raw") -> None:
        self.storage = storage
        self.file_format = file_format
        self.prefix = prefix

    def build_key(self, source: str, table: str, load_date: str) -> str:
        return f"{self.prefix}/{source}/{table}/{load_date}/{table}.{self.file_format.extension}"

    def write(self, df: pd.DataFrame, source: str, table: str, load_date: str) -> str:
        key = self.build_key(source, table, load_date)
        return self.storage.put(key, self.file_format.serialize(df))
