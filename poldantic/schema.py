from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Union, get_args, get_origin, List, Dict, Tuple
from pydantic import BaseModel
import polars as pl
import datetime


# --- Field Metadata ---

@dataclass
class FieldInfo:
    dtype: pl.DataType
    nullable: bool = False

    def __repr__(self):
        return f"FieldInfo(dtype={self.dtype}, nullable={self.nullable})"


# --- Python -> Polars dtype mapping ---

PYTHON_TO_POLARS = {
    int: pl.Int64,
    float: pl.Float64,
    str: pl.Utf8,
    bool: pl.Boolean,
    bytes: pl.Binary,
    datetime.date: pl.Date,
    datetime.datetime: pl.Datetime,
}


# --- Internal Helpers ---

def _resolve_fieldinfo(annotation: Any) -> FieldInfo:
    origin = get_origin(annotation)
    args = get_args(annotation)

    if origin is Union and type(None) in args:
        non_none_args = [arg for arg in args if arg is not type(None)]
        if len(non_none_args) == 1:
            inner = _resolve_fieldinfo(non_none_args[0])
            return FieldInfo(inner.dtype, nullable=True)
        return FieldInfo(pl.Object(), nullable=True)

    if origin is Union:
        return FieldInfo(pl.Object(), nullable=True)

    if origin in (list, List):
        if args:
            inner = _resolve_fieldinfo(args[0])
            return FieldInfo(pl.List(inner.dtype), nullable=False)
        return FieldInfo(pl.List(pl.Object), nullable=False)

    if origin in (dict, Dict, tuple, Tuple):
        return FieldInfo(pl.Object(), nullable=False)
    
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        struct = get_polars_struct(annotation)
        return FieldInfo(struct, nullable=False)

    return FieldInfo(PYTHON_TO_POLARS.get(annotation, pl.Object), nullable=False)


def _get_fieldinfo_items(model_cls: type[BaseModel]) -> list[tuple[str, FieldInfo]]:
    return [
        (name, _resolve_fieldinfo(annotation))
        for name, annotation in model_cls.__annotations__.items()
    ]


# --- Public API ---

def get_polars_fieldinfo_dict(model_cls: type[BaseModel]) -> dict[str, FieldInfo]:
    """Return a dict of field names to FieldInfo objects."""
    return dict(_get_fieldinfo_items(model_cls))


def get_polars_fieldinfo_list(model_cls: type[BaseModel]) -> list[tuple[str, FieldInfo]]:
    """Return a list of (field name, FieldInfo) pairs."""
    return _get_fieldinfo_items(model_cls)


def get_polars_schema_dict(model_cls: type[BaseModel]) -> dict[str, pl.DataType]:
    """Return a dict of field names to Polars dtypes (no nullability info)."""
    return {name: info.dtype for name, info in _get_fieldinfo_items(model_cls)}


def get_polars_schema_list(model_cls: type[BaseModel]) -> list[tuple[str, pl.DataType]]:
    """Return a list of (field name, dtype) tuples (no nullability info)."""
    return [(name, info.dtype) for name, info in _get_fieldinfo_items(model_cls)]


def get_polars_struct(model_cls: type[BaseModel]) -> pl.Struct:
    """Return a pl.Struct dtype representing the nested model."""
    fields = [pl.Field(name, info.dtype) for name, info in _get_fieldinfo_items(model_cls)]
    return pl.Struct(fields)


def get_polars_schema(model_cls: type[BaseModel]) -> pl.Schema:
    """Return a Polars Schema (dict[str, pl.DataType]) for the model."""
    return pl.Schema(get_polars_schema_dict(model_cls))
