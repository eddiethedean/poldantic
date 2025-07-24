from __future__ import annotations
from dataclasses import dataclass
from typing import Any
import polars as pl


@dataclass
class FieldInfo:
    dtype: pl.DataType
    nullable: bool = False
    alias: str | None = None
    default: Any = None
    description: str | None = None

    def __repr__(self):
        return f"FieldInfo(dtype={self.dtype}, nullable={self.nullable})"
