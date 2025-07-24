"""
Convert Pydantic models into Polars schema definitions.

Supports nested models, lists, tuples, enums, and standard Pydantic types including Optional[...] and Annotated.
"""

from typing import Any, Dict, List, Set, Tuple, Type, Union, get_args, get_origin
from pydantic import BaseModel
import polars as pl
import datetime
import enum
import types  # For Python 3.10+ union types like str | None

_PRIMITIVE_POLARS_TYPES = {
    int: pl.Int64,
    float: pl.Float64,
    str: pl.String,
    bool: pl.Boolean,
    bytes: pl.Binary,
    datetime.date: pl.Date,
    datetime.datetime: pl.Datetime,
    datetime.time: pl.Time,
    datetime.timedelta: pl.Duration,
}


def infer_polars_dtype(field_type: Any) -> pl.DataType:
    origin = get_origin(field_type)
    args = get_args(field_type)

    # Handle Optional[T] = Union[T, None] or T | None
    if (origin is Union or origin is types.UnionType) and len(args) == 2 and type(None) in args:
        non_none = next(arg for arg in args if arg is not type(None))
        if non_none in _PRIMITIVE_POLARS_TYPES:
            return _PRIMITIVE_POLARS_TYPES[non_none]
        return infer_polars_dtype(non_none)  # Try deeper inference

    if field_type in _PRIMITIVE_POLARS_TYPES:
        return _PRIMITIVE_POLARS_TYPES[field_type]

    if isinstance(field_type, type):
        if issubclass(field_type, enum.Enum):
            return pl.String
        if issubclass(field_type, BaseModel):
            return infer_polars_schema(field_type)

    # List-like: list, set → pl.List
    if origin in (list, List, set, Set):
        inner = args[0] if args else Any
        if get_origin(inner) in (Union, types.UnionType) and type(None) in get_args(inner):
            inner = next(arg for arg in get_args(inner) if arg is not type(None))
        return pl.List(infer_polars_dtype(inner))

    # Tuple → special handling
    if origin in (tuple, Tuple):
        if len(args) == 2 and args[1] is Ellipsis:
            # Tuple[T, ...]
            return pl.List(infer_polars_dtype(args[0]))
        elif len(set(args)) == 1:
            # Tuple[T, T, ...] → homogeneous
            return pl.List(infer_polars_dtype(args[0]))
        else:
            # Mixed types like Tuple[int, str]
            return pl.Object()

    # Dict fallback
    if origin in (dict, Dict):
        return pl.Object()

    return pl.Object()


def infer_polars_schema(model: Type[BaseModel]) -> pl.Struct:
    fields = []
    for name, field in model.model_fields.items():
        dtype = infer_polars_dtype(field.annotation)
        fields.append((name, dtype))
    return pl.Struct(fields)


def to_polars_schema(model: Type[BaseModel]) -> dict[str, pl.DataType]:
    """
    Convert a Pydantic model into a flat Polars schema dictionary.

    Nested models are converted to pl.Struct objects.
    """
    return {
        name: infer_polars_dtype(field.annotation)
        for name, field in model.model_fields.items()
    }
