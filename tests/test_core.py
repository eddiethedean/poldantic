from typing import List, Optional, Union
from pydantic import BaseModel
import polars as pl
from poldantic import to_polars_schema


def test_simple_schema():
    class User(BaseModel):
        id: int
        name: str
        active: bool

    schema = to_polars_schema(User)
    assert schema == {
        "id": pl.Int64(),
        "name": pl.Utf8(),
        "active": pl.Boolean()
    }


def test_list_field():
    class TagSet(BaseModel):
        tags: list[str]

    schema = to_polars_schema(TagSet)
    assert schema["tags"] == pl.List(pl.Utf8())
