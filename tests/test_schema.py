import polars as pl
from pydantic import BaseModel
from poldantic import get_polars_schema_dict

class MyModel(BaseModel):
    id: int
    name: str

def test_schema_dict():
    schema = get_polars_schema_dict(MyModel)
    assert schema["id"] == pl.Int64
    assert schema["name"] == pl.Utf8
