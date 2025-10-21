import datetime as dt
import enum
import sys
from decimal import Decimal
from typing import Dict, List, Optional, Set, Tuple, Union

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated

import polars as pl
from pydantic import BaseModel, Field

from poldantic.infer_polars import infer_polars_dtype, infer_polars_schema, to_polars_schema


class Role(enum.Enum):
    ADMIN = "admin"
    USER = "user"


class SubModel(BaseModel):
    x: int
    y: float


class Model(BaseModel):
    i: int
    f: float
    s: str
    b: bool
    bin: bytes
    d: dt.date
    dtm: dt.datetime
    tm: dt.time
    dur: dt.timedelta
    dec: Decimal
    opt: Optional[str]
    ann: Annotated[int, Field(gt=0)]
    enum_val: Role
    lst_int: list[int]
    set_str: Set[str]
    tup_homo: Tuple[int, int, int]
    tup_ellipsis: Tuple[str, ...]
    tup_hetero: Tuple[int, str]
    dct: Dict[str, int]
    sub: SubModel
    union_ambig: Union[int, str]
    lst_union: List[Union[int, str]]


def test_primitive_mappings():
    sch = to_polars_schema(Model)
    assert sch["i"] == pl.Int64
    assert sch["f"] == pl.Float64
    # Normalize to pl.String across versions
    assert sch["s"] == pl.String
    assert sch["b"] == pl.Boolean
    assert sch["bin"] == pl.Binary
    assert sch["d"] == pl.Date
    assert sch["dtm"] == pl.Datetime
    assert sch["tm"] == pl.Time
    assert sch["dur"] == pl.Duration
    assert repr(infer_polars_dtype(Decimal)).startswith("Decimal(")


def test_optional_and_annotated_stripped():
    sch = to_polars_schema(Model)
    assert sch["opt"] == pl.String  # Optional[str] strips to underlying dtype
    assert sch["ann"] == pl.Int64  # Annotated[int, ...] strips to int


def test_enum_mapping_prefers_pl_enum_when_available():
    sch = to_polars_schema(Model)
    if hasattr(pl, "Enum"):
        # String-valued enum -> pl.Enum([...]) or fallback pl.String
        assert (str(sch["enum_val"]).startswith("Enum(")) or (sch["enum_val"] == pl.String)
    else:
        assert sch["enum_val"] == pl.String


def test_container_and_tuple_behavior():
    sch = to_polars_schema(Model)
    assert isinstance(sch["lst_int"], pl.List)
    assert sch["lst_int"].inner == pl.Int64

    assert isinstance(sch["set_str"], pl.List)
    assert sch["set_str"].inner == pl.String

    # Homogenous tuples -> List
    assert isinstance(sch["tup_homo"], pl.List)
    assert sch["tup_homo"].inner == pl.Int64

    # Tuple[T, ...] -> List[T]
    assert isinstance(sch["tup_ellipsis"], pl.List)
    assert sch["tup_ellipsis"].inner == pl.String

    # Heterogeneous tuples -> Object
    assert sch["tup_hetero"] == pl.Object()


def test_dict_and_union_fallbacks():
    sch = to_polars_schema(Model)
    assert sch["dct"] == pl.Object()
    assert sch["union_ambig"] == pl.Object()
    assert isinstance(sch["lst_union"], pl.List)
    assert sch["lst_union"].inner == pl.Object()


def test_nested_struct_generation():
    struct_dtype = infer_polars_schema(SubModel)
    assert isinstance(struct_dtype, pl.Struct)
    # Ensure fields are present by name
    names = [
        f[0] if isinstance(f, tuple) else getattr(f, "name", None) for f in struct_dtype.fields
    ]  # compat across polars versions
    assert set(names) == {"x", "y"}

    sch = to_polars_schema(Model)
    assert isinstance(sch["sub"], pl.Struct)
