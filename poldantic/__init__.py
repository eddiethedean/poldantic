"""
Poldantic: Convert Pydantic models into Polars schemas.

This module provides bidirectional conversion between Pydantic and Polars:
- to_polars_schema(model): Converts a Pydantic model into a Polars-compatible schema dict.
- to_pydantic_model(schema): Converts a Polars schema into a Pydantic model.
"""

from .exceptions import (
    InvalidSchemaError,
    PoldanticError,
    SchemaConversionError,
    UnsupportedTypeError,
)
from .infer_polars import to_polars_schema
from .infer_pydantic import to_pydantic_model

__all__ = [
    "to_polars_schema",
    "to_pydantic_model",
    "PoldanticError",
    "SchemaConversionError",
    "UnsupportedTypeError",
    "InvalidSchemaError",
]
__version__ = "0.3.0"
