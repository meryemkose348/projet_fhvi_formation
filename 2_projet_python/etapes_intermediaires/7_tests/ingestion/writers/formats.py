from __future__ import annotations

import io
from abc import ABC, abstractmethod
from typing import ClassVar

import pandas as pd


class FileFormat(ABC):
    extension: ClassVar[str]

    @abstractmethod
    def serialize(self, df: pd.DataFrame) -> bytes:
        """DataFrame -> bytes prêts à stocker"""


class ParquetFormat(FileFormat):
    extension = "parquet"

    def serialize(self, df: pd.DataFrame) -> bytes:
        buffer = io.BytesIO()
        df.to_parquet(buffer, index=False)
        return buffer.getvalue()


class CsvFormat(FileFormat):
    extension = "csv"

    def serialize(self, df: pd.DataFrame) -> bytes:
        return df.to_csv(index=False).encode("utf-8")


FORMATS: dict[str, type[FileFormat]] = {"parquet": ParquetFormat, "csv": CsvFormat}


def get_format(name: str) -> FileFormat:
    try:
        return FORMATS[name]()
    except KeyError:
        raise ValueError(f"Format '{name}' non supporté. Disponibles : {sorted(FORMATS)}") from None
