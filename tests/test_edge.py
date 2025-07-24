from typing import List, Optional, Union, Dict, Tuple
from pydantic import BaseModel, Field, conint
import polars as pl
from poldantic import to_polars_schema


def test_unknown_type_fallback():
    class WeirdType: ...
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
    assert schema["name"] == pl.Utf8()


def test_dict_field_fallback():
    class Model(BaseModel):
        metadata: Dict[str, int]

    schema = to_polars_schema(Model)
    assert schema["metadata"] == pl.Object()


def test_constrained_type():
    class Model(BaseModel):
        age: conint(gt=0)

    schema = to_polars_schema(Model)
    assert schema["age"] == pl.Int64()