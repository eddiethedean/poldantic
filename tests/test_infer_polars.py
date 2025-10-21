from typing import Dict, List, Optional, Tuple, Union

import polars as pl
import pytest
from pydantic import BaseModel, Field, conint

from poldantic.infer_polars import to_polars_schema


def test_simple_schema():
    class User(BaseModel):
        id: int
        name: str
        active: bool

    schema = to_polars_schema(User)
    assert schema == {"id": pl.Int64(), "name": pl.String(), "active": pl.Boolean()}


def test_nested_schema():
    import polars as pl
    from pydantic import BaseModel

    from poldantic.infer_polars import to_polars_schema

    class Address(BaseModel):
        street: str
        zip: int

    class Customer(BaseModel):
        id: int
        address: Address

    schema = to_polars_schema(Customer)
    assert isinstance(schema["address"], pl.Struct)
    assert schema["address"].fields == [
        pl.Field("street", pl.String),
        pl.Field("zip", pl.Int64),
    ]


def test_list_field():
    class TagSet(BaseModel):
        tags: List[str]

    schema = to_polars_schema(TagSet)
    assert schema["tags"] == pl.List(pl.String())


def test_mixed_union_fallback():
    class Event(BaseModel):
        id: Union[int, str]
        payload: Union[int, float, str]
        flag: Union[bool, None]

    schema = to_polars_schema(Event)
    assert schema["id"] == pl.Object
    assert schema["payload"] == pl.Object
    assert schema["flag"] == pl.Boolean()  # Optional[bool] → bool


def test_unknown_type_fallback():
    class WeirdType:
        pass

    class Model(BaseModel):
        data: WeirdType

        model_config = {"arbitrary_types_allowed": True}

    schema = to_polars_schema(Model)
    assert schema["data"] == pl.Object()


def test_union_of_nested_models():
    class A(BaseModel):
        a: int

    class B(BaseModel):
        b: str

    class Wrapper(BaseModel):
        choice: Union[A, B]

    schema = to_polars_schema(Wrapper)
    assert schema["choice"] == pl.Object()


def test_list_of_unions():
    class Item(BaseModel):
        payload: List[Union[int, str]]

    schema = to_polars_schema(Item)
    assert schema["payload"] == pl.List(pl.Object())


def test_deeply_nested_list_of_structs():
    class Point(BaseModel):
        x: float
        y: float

    class Layer(BaseModel):
        points: List[List[Point]]

    schema = to_polars_schema(Layer)
    assert isinstance(schema["points"], pl.List)
    assert isinstance(schema["points"].inner, pl.List)
    assert isinstance(schema["points"].inner.inner, pl.Struct)


def test_optional_list_of_optional_nested():
    class Data(BaseModel):
        value: Optional[List[Optional[int]]]

    schema = to_polars_schema(Data)
    assert schema["value"] == pl.List(pl.Int64())


def test_alias_and_default_fields():
    class Model(BaseModel):
        id: int = Field(default=1, alias="identifier")
        name: str = "unknown"

    schema = to_polars_schema(Model)
    assert schema["id"] == pl.Int64()
    assert schema["name"] == pl.String()


def test_dict_field_fallback():
    class Model(BaseModel):
        metadata: Dict[str, int]

    schema = to_polars_schema(Model)
    assert schema["metadata"] == pl.Object()


def test_custom_email_type():
    pytest.importorskip("email_validator")
    from pydantic import EmailStr

    class Model(BaseModel):
        email: EmailStr

    schema = to_polars_schema(Model)
    assert schema["email"] == pl.Object()


def test_constrained_type():
    class Model(BaseModel):
        age: conint(gt=0)

    schema = to_polars_schema(Model)
    assert schema["age"] == pl.Int64()
