from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel, create_model
import polars as pl
import datetime

POLARS_TO_PYTHON = {
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
    pl.Utf8(): str,
    pl.Boolean(): bool,
    pl.Binary(): bytes,
    pl.Date(): datetime.date,
    pl.Datetime(): datetime.datetime,
    pl.Time(): datetime.time,
    pl.Duration(): int,
}


def _resolve_dtype(
    dtype: Any,
    model_name: str,
    model_cache: Dict[str, Type[BaseModel]],
    force_optional: bool
) -> Any:
    if isinstance(dtype, pl.List):
        inner = _resolve_dtype(dtype.inner, model_name, model_cache, force_optional)
        return List[inner]

    if isinstance(dtype, pl.Struct):
        key = str(dtype)
        if key not in model_cache:
            fields = {}
            for field in dtype.fields:
                field_name = field.name
                field_dtype = field.dtype
                field_type = _resolve_dtype(field_dtype, model_name, model_cache, force_optional)
                fields[field_name] = (
                    (Optional[field_type], None) if force_optional else (field_type, ...)
                )
            model_cache[key] = create_model(f"{model_name}Struct", **fields)
        return model_cache[key]

    return POLARS_TO_PYTHON.get(dtype, Any)


def to_pydantic_model(
    schema: Dict[str, pl.DataType],
    model_name: str = "PolarsModel",
    force_optional: bool = True
) -> Type[BaseModel]:
    """
    Convert a Polars schema dictionary into a Pydantic model.

    Parameters
    ----------
    schema : dict[str, polars.DataType]
        A dictionary mapping field names to Polars data types.
    model_name : str, optional
        The name to assign to the generated Pydantic model class.
    force_optional : bool, default=True
        Whether to wrap all fields in `Optional[...]` to match Polars' nullable semantics.

    Returns
    -------
    Type[pydantic.BaseModel]
        A dynamically created Pydantic model class.

    Examples
    --------
    >>> schema = {'id': pl.Int64, 'name': pl.Utf8}
    >>> Model = to_pydantic_model(schema, "UserModel")
    >>> Model(id=1, name="Alice")
    UserModel(id=1, name='Alice')
    """
    model_cache: Dict[str, Type[BaseModel]] = {}
    fields: Dict[str, tuple[Any, Any]] = {}

    for name, dtype in schema.items():
        py_type = _resolve_dtype(dtype, model_name, model_cache, force_optional)
        fields[name] = (
            (Optional[py_type], None) if force_optional else (py_type, ...)
        )

    return create_model(model_name, **fields)
