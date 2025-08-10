import datetime as dt
from decimal import Decimal
from typing import get_args, Optional

import polars as pl
from pydantic import ValidationError

from poldantic.infer_pydantic import to_pydantic_model


def test_accepts_dtype_classes_and_instances():
    schema = {
        "id": pl.Int64,            # class
        "name": pl.String(),       # instance
        "vals": pl.List(pl.Int32), # mixed inner class
    }
    Model = to_pydantic_model(schema, "T1")
    m = Model(id=1, name="a", vals=[1, 2, 3])
    assert m.id == 1 and m.name == "a" and m.vals == [1, 2, 3]

def test_primitive_roundtrip_targets_python_types():
    schema = {
        "i": pl.Int64,
        "f": pl.Float64(),
        "s": pl.String,
        "b": pl.Boolean(),
        "bin": pl.Binary,
        "d": pl.Date,
        "dtm": pl.Datetime,
        "tm": pl.Time(),
        "dur": pl.Duration,
    }
    Model = to_pydantic_model(schema, "T2")
    m = Model(
        i=1,
        f=1.5,
        s="x",
        b=True,
        bin=b"\x00",
        d=dt.date(2020, 1, 1),
        dtm=dt.datetime(2020, 1, 1, 2, 3, 4),
        tm=dt.time(2, 3, 4),
        dur=dt.timedelta(seconds=5),
    )
    assert m.dur == dt.timedelta(seconds=5)

def test_decimal_maps_to_python_decimal_if_available():
    try:
        schema = {"price": pl.Decimal(38, 18)}
    except Exception:
        # Older Polars may not construct Decimal with given params; skip
        return
    Model = to_pydantic_model(schema, "T3")
    m = Model(price=Decimal("1.23"))
    assert isinstance(m.price, Decimal)

def test_struct_builds_nested_model_and_lists_work():
    # Construct a small struct dtype that should be accepted by our resolver
    sub_struct = pl.Struct([("x", pl.Int64), ("y", pl.Float64)])
    schema = {
        "sub": sub_struct,
        "scores": pl.List(pl.Int32()),
    }
    Parent = to_pydantic_model(schema, "T4")

    inst = Parent(sub={"x": 1, "y": 2.5}, scores=[1, 2, 3])
    assert inst.sub.x == 1 and inst.sub.y == 2.5

def test_force_optional_wraps_fields_by_default():
    schema = {"a": pl.Int64}
    Model = to_pydantic_model(schema, "T5")  # default force_optional=True
    # All fields optional, so creating with missing 'a' should succeed
    assert Model().a is None

def test_force_optional_false_requires_fields():
    schema = {"a": pl.Int64}
    Model = to_pydantic_model(schema, "T6", force_optional=False)
    try:
        Model()
        assert False, "Expected ValidationError when force_optional=False and field missing"
    except ValidationError:
        pass
