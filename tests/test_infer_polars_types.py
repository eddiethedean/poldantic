import datetime
import enum
import polars as pl
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from pydantic import BaseModel

from poldantic.infer_polars import infer_polars_dtype, to_polars_schema


# --- Enum for testing ---
class Color(enum.Enum):
    RED = "red"
    GREEN = "green"


# --- Optional primitives using | None ---
def test_str_or_none():
    assert infer_polars_dtype(str | None) == pl.String

def test_int_or_none():
    assert infer_polars_dtype(int | None) == pl.Int64

def test_float_or_none():
    assert infer_polars_dtype(float | None) == pl.Float64

def test_bool_or_none():
    assert infer_polars_dtype(bool | None) == pl.Boolean


# --- Datetime types ---
def test_datetime():
    assert infer_polars_dtype(datetime.datetime) == pl.Datetime

def test_date():
    assert infer_polars_dtype(datetime.date) == pl.Date

def test_time():
    assert infer_polars_dtype(datetime.time) == pl.Time

def test_timedelta():
    assert infer_polars_dtype(datetime.timedelta) == pl.Duration


# --- List-like containers ---
def test_list_of_int():
    dtype = infer_polars_dtype(List[int])
    assert isinstance(dtype, pl.List)
    assert dtype.inner == pl.Int64

def test_tuple_of_str_as_list():
    dtype = infer_polars_dtype(Tuple[str])
    assert isinstance(dtype, pl.List)
    assert dtype.inner == pl.String

def test_set_of_float():
    dtype = infer_polars_dtype(Set[float])
    assert isinstance(dtype, pl.List)
    assert dtype.inner == pl.Float64

def test_tuple_of_two_ints_is_list():
    dtype = infer_polars_dtype(Tuple[int, int])
    assert isinstance(dtype, pl.List)
    assert dtype.inner == pl.Int64


# --- Dicts, Enums, Fallback ---
def test_dict_of_str_to_int():
    dtype = infer_polars_dtype(Dict[str, int])
    assert dtype == pl.Object()

def test_any_type():
    dtype = infer_polars_dtype(Any)
    assert dtype == pl.Object()


def test_union_of_multiple_types_falls_back():
    assert infer_polars_dtype(Union[int, str]) == pl.Object()


# --- Nested struct ---
def test_nested_schema():
    class Address(BaseModel):
        street: str
        zip: int

    class Customer(BaseModel):
        id: int
        address: Address

    schema = to_polars_schema(Customer)
    assert isinstance(schema["address"], pl.Struct)
    assert schema["address"].fields == [
        ("street", pl.String),
        ("zip", pl.Int64)
    ]


# --- Optional[List[Optional[int]]] support ---
def test_optional_list_of_optional_nested():
    class Data(BaseModel):
        value: Optional[List[Optional[int]]]

    schema = to_polars_schema(Data)
    assert schema["value"] == pl.List(pl.Int64)


# --- Tuple fallback test ---
def test_tuple_field_fallback():
    from pydantic import BaseModel
    from typing import Tuple
    from poldantic.infer_polars import to_polars_schema
    import polars as pl

    class Model(BaseModel):
        point: Tuple[int, int]

    schema = to_polars_schema(Model)
    assert schema["point"] == pl.List(pl.Int64)
