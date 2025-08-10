from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import polars as pl


__all__ = ["FieldInfo"]


@dataclass(slots=True)
class FieldInfo:
    """
    Minimal field metadata wrapper for Polars schema fields used by Poldantic.
    """
    dtype: pl.DataType
    nullable: bool = False
    alias: Optional[str] = None
    default: Any = None
    description: Optional[str] = None

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"FieldInfo(dtype={self.dtype}, nullable={self.nullable})"

    @staticmethod
    def of(dtype: pl.DataType, *, nullable: bool = False, **kw: Any) -> "FieldInfo":
        """Convenience constructor."""
        return FieldInfo(dtype=dtype, nullable=nullable, **kw)
