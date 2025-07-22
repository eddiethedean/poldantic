# 🧩 Poldantic

**Poldantic** converts [Pydantic](https://docs.pydantic.dev/) models into [Polars](https://pola.rs/) schemas — making it easy to validate, align, and document your data pipeline types between the Python and Polars worlds.

---

## ✨ Features

- 🔁 Convert `BaseModel` classes to `polars.Schema` or `pl.Struct`
- ✅ Handles optional fields (`Optional[T]`) and union types
- 🧱 Supports nested and deeply nested Pydantic models
- 📦 Outputs multiple formats: `dict`, `list`, `pl.Schema`, `pl.Struct`
- 🧠 Tracks `nullable` status via `FieldInfo`

---

## 📦 Installation

```bash
pip install poldantic
```

---

## 🚀 Usage

```python
from pydantic import BaseModel
from typing import Optional, List
import polars as pl
import poldantic as pd

class Address(BaseModel):
    street: str
    zip: Optional[int]

class User(BaseModel):
    id: int
    name: str
    address: Address
    tags: List[str]

pd.get_polars_schema_dict(User)
# {'id': pl.Int64, 'name': pl.Utf8, 'address': pl.Struct([...]), 'tags': pl.List(pl.Utf8)}

pd.get_polars_schema(User)
# pl.Schema({...})

pd.get_polars_struct(User)
# pl.Struct([...])

pd.get_polars_fieldinfo_dict(User)
# {'name': FieldInfo(dtype=Utf8, nullable=False), ...}
```

---

## 🧪 Output Formats

| Function | Output |
|----------|--------|
| `get_polars_schema_dict()` | `dict[str, pl.DataType]` |
| `get_polars_schema_list()` | `list[(str, pl.DataType)]` |
| `get_polars_fieldinfo_dict()` | `dict[str, FieldInfo]` |
| `get_polars_fieldinfo_list()` | `list[(str, FieldInfo)]` |
| `get_polars_schema()` | `pl.Schema` |
| `get_polars_struct()` | `pl.Struct` |

---

## 🔍 FieldInfo

The `FieldInfo` object tracks both the Polars data type and its nullability:

```python
@dataclass
class FieldInfo:
    dtype: pl.DataType
    nullable: bool = False
```

---

## 📚 Examples

See [`examples/poldantic_demo.ipynb`](examples/poldantic_demo.ipynb) for a working notebook showing nested models and schema inspection.

---

## 📜 License

MIT License © 2025 Odos Matthews
