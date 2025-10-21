"""
Pydantic ➜ Polars schema inference.

- Handles Optional, Annotated, containers (list/set/tuple), nested models, enums.
- Ambiguous unions (e.g., Union[int, str]) fall back to pl.Object (per project preference).
- String is normalized to pl.String.
"""

from __future__ import annotations

import datetime as _dt
import enum
import sys
import types as _types  # for the `|` style unions in 3.10+
from contextvars import ContextVar
from dataclasses import dataclass, replace
from decimal import Decimal
from typing import Any, Dict, List, Optional, Set, Tuple, Type, Union, get_args, get_origin

try:
    from typing import Annotated  # Python 3.9+
except ImportError:
    from typing_extensions import Annotated  # Python 3.8

import polars as pl
from pydantic import BaseModel

# UnionType is only available in Python 3.10+
if sys.version_info >= (3, 10):
    _UNION_TYPES = (Union, _types.UnionType)
else:
    _UNION_TYPES = (Union,)

__all__ = [
    "to_polars_schema",
    "infer_polars_schema",
    "infer_polars_dtype",
    "Settings",
    "settings",
    "get_settings",
    "set_settings",
]


# ------------------------- Settings -------------------------


if sys.version_info >= (3, 10):

    @dataclass(frozen=True, slots=True)
    class Settings:
        """
        Tunable knobs for inference behavior.

        Settings are immutable and thread-safe using contextvars.
        To change settings, create a new Settings instance and use set_settings().
        """

        use_pl_enum_for_string_enums: bool = True
        decimal_precision: int = 38
        decimal_scale: int = 18
        uuid_as_string: bool = True

        def copy(self, **changes: Any) -> Settings:
            """Create a copy of settings with specified changes."""
            return replace(self, **changes)

else:

    @dataclass(frozen=True)
    class Settings:
        """
        Tunable knobs for inference behavior.

        Settings are immutable and thread-safe using contextvars.
        To change settings, create a new Settings instance and use set_settings().
        """

        use_pl_enum_for_string_enums: bool = True
        decimal_precision: int = 38
        decimal_scale: int = 18
        uuid_as_string: bool = True

        def copy(self, **changes: Any) -> Settings:
            """Create a copy of settings with specified changes."""
            return replace(self, **changes)


# Global default settings
_DEFAULT_SETTINGS = Settings()

# Context-local settings (for thread/async safety)
_settings_context: ContextVar[Optional[Settings]] = ContextVar("poldantic_settings", default=None)


def get_settings() -> Settings:
    """Get current settings (context-aware)."""
    ctx_settings = _settings_context.get()
    return ctx_settings if ctx_settings is not None else _DEFAULT_SETTINGS


def set_settings(new_settings: Settings) -> None:
    """Set settings for current context."""
    _settings_context.set(new_settings)


# Backward compatibility: module-level settings object
# This acts as a proxy to get_settings() for attribute access
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


# ------------------------- Primitives -------------------------


def _decimal_dtype() -> pl.DataType:
    s = get_settings()
    try:
        return pl.Decimal(s.decimal_precision, s.decimal_scale)
    except Exception:
        # Older Polars or environments without Decimal support
        return pl.Object()


_PRIMITIVE_POLARS_TYPES: Dict[Type[Any], pl.DataType] = {
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

# UUID type (if available)
_UUID_TYPE = None
try:
    import uuid

    _UUID_TYPE = uuid.UUID
except Exception:
    pass


def _get_uuid_dtype() -> pl.DataType:
    """Get UUID dtype based on current settings."""
    return pl.String if get_settings().uuid_as_string else pl.Object()


# ------------------------- Helpers -------------------------


def _strip_annotated(tp: Any) -> Any:
    if get_origin(tp) is Annotated:
        args = get_args(tp)
        return args[0] if args else tp
    return tp


def _optional_inner(tp: Any) -> Tuple[Any, bool]:
    """If Optional[T], return (T, True); else (tp, False)."""
    origin = get_origin(tp)
    if origin in _UNION_TYPES:
        args = tuple(get_args(tp))
        if len(args) >= 2 and type(None) in args:
            non_none = [a for a in args if a is not type(None)]
            if len(non_none) == 1:
                return non_none[0], True
    return tp, False


def _enum_dtype(et: type[enum.Enum]) -> pl.DataType:
    # Prefer pl.Enum for string-valued enums when available and enabled.
    s = get_settings()
    if not s.use_pl_enum_for_string_enums or not hasattr(pl, "Enum"):
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

    # UUID type (dynamic based on settings)
    if _UUID_TYPE is not None and field_type is _UUID_TYPE:
        return _get_uuid_dtype()

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
    if origin in _UNION_TYPES:
        return pl.Object()

    # Unknown -> Object
    return pl.Object()


def infer_polars_schema(model: Type[BaseModel]) -> pl.Struct:
    """
    Build a pl.Struct dtype for a (nested) Pydantic model.
    """
    # Pydantic v2 API: model.model_fields
    fields: List[pl.Field] = []
    for name, fld in model.model_fields.items():
        fields.append(pl.Field(name, infer_polars_dtype(fld.annotation)))
    return pl.Struct(fields)


def to_polars_schema(model: Type[BaseModel]) -> Dict[str, pl.DataType]:
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
    return {name: infer_polars_dtype(fld.annotation) for name, fld in model.model_fields.items()}
