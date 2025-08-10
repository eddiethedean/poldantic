"""
Pydantic ➜ Polars schema inference.

- Handles Optional, Annotated, containers (list/set/tuple), nested models, enums.
- Ambiguous unions (e.g., Union[int, str]) fall back to pl.Object (per project preference).
- String is normalized to pl.String.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Any, Dict, List, Set, Tuple, Type, Union, get_args, get_origin

import datetime as _dt
import enum
import types as _types  # for the `|` style unions in 3.10+
from decimal import Decimal

import polars as pl
from pydantic import BaseModel


__all__ = [
    "to_polars_schema",
    "infer_polars_schema",
    "infer_polars_dtype",
    "Settings",
    "settings",
]


# ------------------------- Settings -------------------------

@dataclass(slots=True)
class Settings:
    """Tunable knobs for inference behavior."""
    use_pl_enum_for_string_enums: bool = True
    decimal_precision: int = 38
    decimal_scale: int = 18
    uuid_as_string: bool = True


settings = Settings()


# ------------------------- Primitives -------------------------

def _decimal_dtype() -> pl.DataType:
    try:
        return pl.Decimal(settings.decimal_precision, settings.decimal_scale)
    except Exception:
        # Older Polars or environments without Decimal support
        return pl.Object()


_PRIMITIVE_POLARS_TYPES: dict[type[Any], pl.DataType] = {
    int: pl.Int64,
    float: pl.Float64,
    str: pl.String,
    bool: pl.Boolean,
    bytes: pl.Binary,
    _dt.date: pl.Date,
    _dt.datetime: pl.Datetime,
    _dt.time: pl.Time,
    _dt.timedelta: pl.Duration,
    Decimal: _decimal_dtype(),
}

try:
    import uuid
    _PRIMITIVE_POLARS_TYPES[uuid.UUID] = pl.String if settings.uuid_as_string else pl.Object()
except Exception:
    pass


# ------------------------- Helpers -------------------------

def _strip_annotated(tp: Any) -> Any:
    if get_origin(tp) is Annotated:
        args = get_args(tp)
        return args[0] if args else tp
    return tp


def _optional_inner(tp: Any) -> tuple[Any, bool]:
    """If Optional[T], return (T, True); else (tp, False)."""
    origin = get_origin(tp)
    if origin in (Union, _types.UnionType):
        args = tuple(get_args(tp))
        if len(args) >= 2 and type(None) in args:
            non_none = [a for a in args if a is not type(None)]
            if len(non_none) == 1:
                return non_none[0], True
    return tp, False


def _enum_dtype(et: type[enum.Enum]) -> pl.DataType:
    # Prefer pl.Enum for string-valued enums when available and enabled.
    if not settings.use_pl_enum_for_string_enums or not hasattr(pl, "Enum"):
        return pl.String
    values = [e.value for e in et]
    if all(isinstance(v, str) for v in values):
        try:
            return pl.Enum(values)  # type: ignore[attr-defined]
        except Exception:
            pass
    return pl.String


# ------------------------- Inference -------------------------

def infer_polars_dtype(field_type: Any) -> pl.DataType:
    """
    Infer a Polars dtype from a Python/typing/Pydantic annotation.
    """
    field_type = _strip_annotated(field_type)
    field_type, _ = _optional_inner(field_type)

    # Direct primitive map
    if field_type in _PRIMITIVE_POLARS_TYPES:
        return _PRIMITIVE_POLARS_TYPES[field_type]

    # Pydantic models -> Struct
    if isinstance(field_type, type):
        if issubclass(field_type, enum.Enum):
            return _enum_dtype(field_type)
        if issubclass(field_type, BaseModel):
            return infer_polars_schema(field_type)

    origin = get_origin(field_type)
    args = get_args(field_type)

    # list/set -> pl.List(inner)
    if origin in (list, List, set, Set):
        inner = args[0] if args else Any
        inner = _strip_annotated(inner)
        inner, _ = _optional_inner(inner)
        return pl.List(infer_polars_dtype(inner))

    # tuple handling
    if origin in (tuple, Tuple):
        if len(args) == 2 and args[1] is Ellipsis:
            # Tuple[T, ...]
            return pl.List(infer_polars_dtype(_strip_annotated(args[0])))
        if len(args) > 0 and len(set(args)) == 1:
            # Tuple[T, T, ...] homogeneous -> List[T]
            return pl.List(infer_polars_dtype(_strip_annotated(args[0])))
        # Heterogeneous tuples
        return pl.Object()

    # dict -> Object (arbitrary keys)
    if origin in (dict, Dict):
        return pl.Object()

    # Non-optional unions (e.g., Union[int, str]) -> Object
    if origin in (Union, _types.UnionType):
        return pl.Object()

    # Unknown -> Object
    return pl.Object()


def infer_polars_schema(model: Type[BaseModel]) -> pl.Struct:
    """
    Build a pl.Struct dtype for a (nested) Pydantic model.
    """
    # Pydantic v2 API: model.model_fields
    fields: list[tuple[str, pl.DataType]] = []
    for name, fld in model.model_fields.items():
        fields.append((name, infer_polars_dtype(fld.annotation)))
    return pl.Struct(fields)


def to_polars_schema(model: Type[BaseModel]) -> dict[str, pl.DataType]:
    """
    Infer a flat Polars schema dictionary from a Pydantic model.

    This inspects the type annotations (and nested model structure) of the
    given Pydantic model and maps each field to an appropriate Polars
    `pl.DataType`. Nested Pydantic submodels are represented as `pl.Struct`
    dtypes with their own inferred inner fields.

    Parameters
    ----------
    model : Type[pydantic.BaseModel]
        A Pydantic model class (not an instance) to inspect.

    Returns
    -------
    dict[str, pl.DataType]
        Mapping of field names to Polars dtypes suitable for use in
        `polars.DataFrame` creation or schema validation.

    Notes
    -----
    - Optional[...] annotations are unwrapped before mapping.
    - Container types (list, set, tuple) map to `pl.List(inner_dtype)` if
      homogeneous, otherwise fall back to `pl.Object()`.
    - Ambiguous unions (e.g., Union[int, str]) fall back to `pl.Object()`.
    - `Enum` subclasses map to `pl.String()`.

    Examples
    --------
    >>> from pydantic import BaseModel
    >>> from typing import Optional, List
    >>> import polars as pl
    >>> class User(BaseModel):
    ...     id: int
    ...     name: str
    ...     tags: Optional[List[str]]
    >>> to_polars_schema(User)
    {'id': pl.Int64, 'name': pl.String, 'tags': pl.List(pl.String)}
    """
    return {
        name: infer_polars_dtype(fld.annotation)
        for name, fld in model.model_fields.items()}
