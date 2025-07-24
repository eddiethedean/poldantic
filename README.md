# 🧩 Poldantic

> Convert [Pydantic](https://docs.pydantic.dev/) models into [Polars](https://pola.rs) schemas — and back again.

Poldantic bridges the world of **data validation** (via Pydantic) and **blazing-fast computation** (via Polars). It's ideal for type-safe ETL pipelines, FastAPI response models, and schema round-tripping between Python classes and dataframes.

---

## ✨ Features

- 🔁 **Bidirectional conversion**: Pydantic models ⇄ Polars schemas
- 🧠 Smart support for nested models, lists, sets, tuples, enums, and optional fields
- 🛠 Handles complex edge cases with minimal fallback to `pl.Object`
- 🧪 100% test coverage with edge-case and structural schema tests
- ⚙️ Minimal dependencies and easy integration into production pipelines

---

## 📦 Installation

```bash
pip install poldantic
```

Supports **Python 3.8+** and **Polars ≥ 0.19**.

---

## 🚀 Usage

### 🔄 Pydantic → Polars

```python
from poldantic import to_polars_schema
from pydantic import BaseModel
from typing import Optional, List

class Person(BaseModel):
    name: str
    tags: Optional[List[str]]

schema = to_polars_schema(Person)
print(schema)
```

**Output:**

```python
{'name': Utf8, 'tags': List[Utf8]}
```

---

### 🔄 Polars → Pydantic

```python
from poldantic import to_pydantic_model
import polars as pl

schema = {
    "name": pl.Utf8,
    "tags": pl.List(pl.Utf8),
}

Model = to_pydantic_model(schema)
print(Model(name="Alice", tags=["x", "y"]))
```

**Output:**

```python
name='Alice' tags=['x', 'y']
```

---

### 🧬 Nested Models

```python
class Address(BaseModel):
    street: str
    zip: int

class Customer(BaseModel):
    id: int
    address: Address

to_polars_schema(Customer)
```

**Output:**

```python
{
  'id': Int64,
  'address': Struct([('street', Utf8), ('zip', Int64)])
}
```

---

## ⚙️ API Reference

```python
to_polars_schema(model: Type[BaseModel]) -> dict[str, pl.DataType]
```

Converts a Pydantic model into a Polars-compatible schema dictionary. Supports nested models as `pl.Struct(...)`.

---

```python
to_pydantic_model(
    schema: dict[str, pl.DataType],
    model_name: str = "PolarsModel",
    force_optional: bool = True
) -> Type[BaseModel]
```

Converts a Polars schema dict into a Pydantic model. All fields are wrapped in `Optional[...]` by default to match Polars' nullability semantics.

---

## 📚 Supported Type Mappings

| Pydantic Type           | Polars Type        |
|-------------------------|--------------------|
| `int`                   | `pl.Int64()`       |
| `float`                 | `pl.Float64()`     |
| `str`                   | `pl.String()` or `pl.Utf8()` |
| `bool`                  | `pl.Boolean()`     |
| `bytes`                 | `pl.Binary()`      |
| `datetime.date`         | `pl.Date()`        |
| `datetime.datetime`     | `pl.Datetime()`    |
| `datetime.time`         | `pl.Time()`        |
| `datetime.timedelta`    | `pl.Duration()`    |
| `Enum` subclasses       | `pl.String()`      |
| `List[T]`, `Set[T]`, `Tuple[T, ...]` | `pl.List(T)`  |
| Nested Pydantic model   | `pl.Struct(...)`   |
| `Union[int, str]`, `Any`| `pl.Object()`      |

---

## 🧪 Running Tests

To run the test suite:

```bash
pytest
```

Tests cover a wide variety of primitives, nested models, optional fields, container types, and edge cases.

---

## 📄 License

MIT License © 2025 [Odos Matthews](https://github.com/odosmatthews)

---

## 💡 Tip

Poldantic is an ideal companion for tools like [Articuno](https://github.com/your-org/articuno) and [FastAPI](https://fastapi.tiangolo.com/) — enabling full-circle schema validation and type-checking between APIs and DataFrames.