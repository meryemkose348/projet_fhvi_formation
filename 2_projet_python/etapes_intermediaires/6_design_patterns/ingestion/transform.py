from __future__ import annotations

import re

import pandas as pd


def to_snake_case(name: str) -> str:
    name = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", name.strip())
    return re.sub(r"[^0-9a-zA-Z]+", "_", name).strip("_").lower()


def _strip(value):
    return value.strip() if isinstance(value, str) else value


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    result = df.rename(columns=to_snake_case)
    for column in result.select_dtypes(include="object").columns:
        result[column] = result[column].map(_strip)
    return result
