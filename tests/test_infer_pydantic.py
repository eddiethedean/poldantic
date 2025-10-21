import polars as pl
import pytest
from pydantic import BaseModel, ValidationError

from poldantic.infer_pydantic import to_pydantic_model


def test_flat_schema_required_fields():
    schema = {"id": pl.Int64(), "name": pl.Utf8(), "active": pl.Boolean()}
    Model = to_pydantic_model(schema, "UserModel", force_optional=False)
    instance = Model(id=1, name="Alice", active=True)
    assert instance.name == "Alice"
    try:
        Model(id=1, active=True)
        pytest.fail("Missing field should raise error")
    except ValidationError:
        pass


def test_flat_schema_optional_fields():
    schema = {"id": pl.Int64(), "name": pl.Utf8(), "active": pl.Boolean()}
    Model = to_pydantic_model(schema, "UserModelOpt", force_optional=True)
    instance = Model()
    assert instance.id is None
    assert instance.name is None
    assert instance.active is None


def test_nested_optional_struct():
    schema = {"location": pl.Struct([pl.Field("lat", pl.Float64()), pl.Field("lon", pl.Float64())])}
    Model = to_pydantic_model(schema, "GeoModelOpt")
    instance = Model()
    assert instance.location is None


def test_list_of_structs_optional():
    point_struct = pl.Struct([pl.Field("x", pl.Float64()), pl.Field("y", pl.Float64())])
    schema = {"points": pl.List(point_struct)}
    Model = to_pydantic_model(schema, "PointsModelOpt", force_optional=True)
    instance = Model()
    assert instance.points is None


def test_required_nested_struct_fields():
    schema = {"coords": pl.Struct([pl.Field("lat", pl.Float64()), pl.Field("lon", pl.Float64())])}
    Model = to_pydantic_model(schema, "CoordsModel", force_optional=False)
    try:
        Model(coords={"lat": 1.0})
        pytest.fail("Missing nested field should raise error")
    except ValidationError:
        pass
