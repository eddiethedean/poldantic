"""
Polars schema ➜ Pydantic model inference.

- Accepts dtype classes (pl.Int64) or instances (pl.Int64()) interchangeably.
- Lists and Structs resolve recursively.
- Fields are Optional[...] by default, mirroring Polars' nullable-by-default semantics.
"""

from __future__ import annotations

import datetime as _dt
import sys
from contextvars import ContextVar
from dataclasses import dataclass, replace
from decimal import Decimal as _Decimal
from typing import Any, Dict, List, Optional, Tuple, Type

import polars as pl
from pydantic import BaseModel, create_model

__all__ = ["to_pydantic_model", "Settings", "settings", "get_settings", "set_settings"]


# ------------------------- Settings -------------------------


if sys.version_info >= (3, 10):

    @dataclass(frozen=True, slots=True)
    class Settings:
        """
        Tunable knobs for reverse inference behavior.

        Settings are immutable and thread-safe using contextvars.
        To change settings, create a new Settings instance and use set_settings().
        """

        decimal_precision: int = 38
        decimal_scale: int = 18
        durations_as_timedelta: bool = True
        treat_enum_as_str: bool = True  # Polars Enum/Categorical ➜ str in Pydantic

        def copy(self, **changes: Any) -> Settings:
            """Create a copy of settings with specified changes."""
            return replace(self, **changes)

else:

    @dataclass(frozen=True)
    class Settings:
        """
        Tunable knobs for reverse inference behavior.

        Settings are immutable and thread-safe using contextvars.
        To change settings, create a new Settings instance and use set_settings().
        """

        decimal_precision: int = 38
        decimal_scale: int = 18
        durations_as_timedelta: bool = True
        treat_enum_as_str: bool = True  # Polars Enum/Categorical ➜ str in Pydantic

        def copy(self, **changes: Any) -> Settings:
            """Create a copy of settings with specified changes."""
            return replace(self, **changes)


# Global default settings
_DEFAULT_SETTINGS = Settings()

# Context-local settings (for thread/async safety)
_settings_context: ContextVar[Optional[Settings]] = ContextVar(
    "poldantic_pydantic_settings", default=None
)


def get_settings() -> Settings:
    """Get current settings (context-aware)."""
    ctx_settings = _settings_context.get()
    return ctx_settings if ctx_settings is not None else _DEFAULT_SETTINGS


def set_settings(new_settings: Settings) -> None:
    """Set settings for current context."""
    _settings_context.set(new_settings)


# Backward compatibility: module-level settings object
class _SettingsProxy:
    """Proxy object that forwards attribute access to context-aware settings."""

    def __getattr__(self, name: str) -> Any:
        return getattr(get_settings(), name)

    def __setattr__(self, name: str, value: Any) -> None:
        # For backward compatibility, update the context
        current = get_settings()
        new_settings = current.copy(**{name: value})
        set_settings(new_settings)


settings = _SettingsProxy()


# ------------------------- Helpers -------------------------


def _as_instance(dtype: Any) -> Any:
    """
    Normalize a Polars dtype to an *instance* so isinstance checks work uniformly.
    Leaves pl.List/pl.Struct intact.
    """
    if isinstance(dtype, (pl.List, pl.Struct)):
        return dtype

    # Known primitive classes are callable to produce instances; call defensively.
    try:
        known = {
            pl.Int8,
            pl.Int16,
            pl.Int32,
            pl.Int64,
            pl.UInt8,
            pl.UInt16,
            pl.UInt32,
            pl.UInt64,
            pl.Float32,
            pl.Float64,
            getattr(pl, "Utf8", None),
            getattr(pl, "String", None),
            pl.Boolean,
            pl.Binary,
            pl.Date,
            pl.Datetime,
            pl.Time,
            pl.Duration,
        }
        known = {k for k in known if k is not None}
        if dtype in known:
            return dtype()
    except Exception:
        pass
    return dtype


def _decimal_instance() -> Any:
    s = get_settings()
    try:
        return pl.Decimal(s.decimal_precision, s.decimal_scale)
    except Exception:
        return None


# ------------------------- Core mapping -------------------------


def _get_duration_type() -> type:
    """Get Duration type mapping based on current settings."""
    return _dt.timedelta if get_settings().durations_as_timedelta else int


_POLARS_TO_PYTHON: Dict[Any, Type[Any]] = {
    pl.Int8(): int,
    pl.Int16(): int,
    pl.Int32(): int,
    pl.Int64(): int,
    pl.UInt8(): int,
    pl.UInt16(): int,
    pl.UInt32(): int,
    pl.UInt64(): int,
    pl.Float32(): float,
    pl.Float64(): float,
    (getattr(pl, "Utf8", pl.String))(): str,
    pl.String(): str,
    pl.Boolean(): bool,
    pl.Binary(): bytes,
    pl.Date(): _dt.date,
    pl.Datetime(): _dt.datetime,
    pl.Time(): _dt.time,
}

# Decimal (if available)
_dec = _decimal_instance()
if _dec is not None:
    _POLARS_TO_PYTHON[_dec] = _Decimal

# Categorical/Enum (map to str for Pydantic)
if hasattr(pl, "Categorical"):
    try:
        _POLARS_TO_PYTHON[pl.Categorical()] = str
    except Exception:
        pass
if hasattr(pl, "Enum"):
    try:
        _POLARS_TO_PYTHON[pl.Enum([])] = str
    except Exception:
        pass


# ------------------------- Resolution -------------------------


def _iter_struct_fields(sf: pl.Struct):
    """Yield (name, dtype) for struct fields, accepting tuple- or Field-based representations."""
    for f in sf.fields:
        if isinstance(f, tuple):  # e.g. ("x", pl.Int64)
            yield f[0], f[1]
        else:  # polars.Field-like
            yield f.name, f.dtype


def _resolve_dtype(
    dtype: Any,
    model_name: str,
    model_cache: Dict[Any, Type[BaseModel]],
    force_optional: bool,
) -> Any:
    dtype = _as_instance(dtype)

    if isinstance(dtype, pl.List):
        inner = _resolve_dtype(dtype.inner, model_name, model_cache, force_optional)
        return List[inner]

    if isinstance(dtype, pl.Struct):
        # Build a stable, representation-free cache key
        key = ("Struct", tuple((n, type(dt), str(dt)) for n, dt in _iter_struct_fields(dtype)))
        if key not in model_cache:
            fields: Dict[str, Tuple[Any, Any]] = {}
            for fname, fdtype in _iter_struct_fields(dtype):
                f_type = _resolve_dtype(fdtype, model_name, model_cache, force_optional)
                fields[fname] = (Optional[f_type], None) if force_optional else (f_type, ...)
            model_cache[key] = create_model(f"{model_name}Struct", **fields)
        return model_cache[key]

    # Handle Duration dynamically based on settings
    if isinstance(dtype, pl.Duration):
        return _get_duration_type()

    # Primitive/fallback
    return _POLARS_TO_PYTHON.get(dtype, Any)


# ------------------------- Public API -------------------------


def to_pydantic_model(
    schema: Dict[str, pl.DataType],
    model_name: str = "PolarsModel",
    force_optional: bool = True,
) -> Type[BaseModel]:
    """
    Create a Pydantic model from a Polars schema dictionary.

    This inspects a mapping of field names to Polars dtypes and constructs a
    new `pydantic.BaseModel` subclass with matching field names and types.
    Nested `pl.Struct` and `pl.List` types are resolved recursively into
    nested Pydantic models and typed lists.

    Parameters
    ----------
    schema : dict[str, pl.DataType]
        Field name to Polars dtype mapping. Dtypes may be specified as either
        Polars dtype *classes* (e.g. `pl.Int64`) or dtype *instances*
        (e.g. `pl.Int64()`).
    model_name : str, default="PolarsModel"
        The name assigned to the generated Pydantic model class.
    force_optional : bool, default=True
        If True, wraps all field types in `Optional[...]` to reflect Polars'
        nullable-by-default semantics. If False, all fields are required.

    Returns
    -------
    Type[pydantic.BaseModel]
        A dynamically generated Pydantic model class.

    Notes
    -----
    - `pl.List(inner)` maps to `list[inner_type]`.
    - `pl.Struct([...])` maps to a nested Pydantic model.
    - Unsupported or ambiguous dtypes map to `typing.Any`.
    - Reuses nested model definitions via an internal cache for repeated
      struct shapes.

    Examples
    --------
    >>> import polars as pl
    >>> schema = {
    ...     'id': pl.Int64,
    ...     'name': pl.String,
    ...     'tags': pl.List(pl.String())
    ... }
    >>> Model = to_pydantic_model(schema, model_name="UserModel")
    >>> Model(id=1, name="Alice", tags=["x", "y"])
    UserModel(id=1, name='Alice', tags=['x', 'y'])
    """
    model_cache: Dict[Any, Type[BaseModel]] = {}
    fields: Dict[str, Tuple[Any, Any]] = {}

    for name, dtype in schema.items():
        py_type = _resolve_dtype(dtype, model_name, model_cache, force_optional)
        fields[name] = (Optional[py_type], None) if force_optional else (py_type, ...)

    return create_model(model_name, **fields)
