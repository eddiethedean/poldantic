"""
Poldantic: Convert Pydantic models into Polars schemas.

This module provides a single top-level function:
- to_polars_schema(model): Converts a Pydantic model into a Polars-compatible schema dict.
"""

from .infer_polars import to_polars_schema
from .infer_pydantic import to_pydantic_model

__all__ = ["to_polars_schema", "to_pydantic_model"]
__version__ = "0.2.2"
