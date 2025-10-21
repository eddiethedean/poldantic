# 🧩 Poldantic

[![PyPI version](https://badge.fury.io/py/poldantic.svg)](https://badge.fury.io/py/poldantic)
[![Python versions](https://img.shields.io/pypi/pyversions/poldantic.svg)](https://pypi.org/project/poldantic/)
[![Tests](https://github.com/eddiethedean/poldantic/workflows/Tests/badge.svg)](https://github.com/eddiethedean/poldantic/actions)
[![codecov](https://codecov.io/gh/eddiethedean/poldantic/branch/main/graph/badge.svg)](https://codecov.io/gh/eddiethedean/poldantic)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> Convert [Pydantic](https://docs.pydantic.dev/) models into [Polars](https://pola.rs) schemas — and back again.

Poldantic bridges the world of **data validation** (Pydantic) and **blazing-fast computation** (Polars). It's ideal for type-safe ETL pipelines, FastAPI response models, and schema round-tripping between Python classes and DataFrames.

---

## ✨ Features

- 🔁 **Bidirectional conversion** — Pydantic models ⇄ Polars schemas
- 🧠 **Smart type handling** — nested models, containers (`list`, `set`, `tuple`), enums, `Optional`, `Annotated`, and more
- 🔒 **Thread-safe settings** — context-aware configuration using `contextvars` for concurrent environments
- 🛡️ **Custom exceptions** — clear error messages for conversion failures and type mismatches
- 🛠 **Sensible fallbacks** — ambiguous types like `Union[int, str]` map to `pl.Object()`
- 🧪 **Thoroughly tested** — 47+ tests covering primitives, containers, structs, enums, and round-trip inference
- 📦 **Minimal dependencies** — Pydantic v2+, Polars ≥ 0.20, Python 3.8+ — production‑ready
- 🎯 **Type-safe** — full mypy coverage with strict type checking

---

## 📦 Install

```bash
pip install poldantic
```

**Requires:** Python ≥ 3.8, Pydantic ≥ 2.0, Polars ≥ 0.20.0

---

## 🚀 Quick Start

```python
from typing import Optional, List
from pydantic import BaseModel
import polars as pl
from poldantic import to_polars_schema, to_pydantic_model

# Define a Pydantic model
class User(BaseModel):
    id: int
    name: str
    tags: Optional[List[str]] = None

# Convert to Polars schema
schema = to_polars_schema(User)
# {'id': Int64, 'name': String, 'tags': List(String)}

# Create a DataFrame
df = pl.DataFrame([
    {"id": 1, "name": "Alice", "tags": ["python", "rust"]},
    {"id": 2, "name": "Bob", "tags": None}
], schema=schema)

# Convert Polars schema back to Pydantic
polars_schema = df.schema
GeneratedModel = to_pydantic_model(polars_schema, "GeneratedModel")
instance = GeneratedModel(id=3, name="Charlie", tags=["go"])
```

---

## 📖 Usage Guide

> 💡 **See also**: Interactive Jupyter notebooks in the [`examples/`](https://github.com/eddiethedean/poldantic/tree/main/examples) directory:
> - [`01_basic_usage.ipynb`](https://github.com/eddiethedean/poldantic/blob/main/examples/01_basic_usage.ipynb) - Core functionality and round-trip conversions
> - [`02_advanced_types.ipynb`](https://github.com/eddiethedean/poldantic/blob/main/examples/02_advanced_types.ipynb) - Nested models, enums, and complex types
> - [`03_settings_configuration.ipynb`](https://github.com/eddiethedean/poldantic/blob/main/examples/03_settings_configuration.ipynb) - Customizing behavior with settings
> - [`04_fastapi_integration.ipynb`](https://github.com/eddiethedean/poldantic/blob/main/examples/04_fastapi_integration.ipynb) - Building APIs with FastAPI
> - [`05_etl_pipeline.ipynb`](https://github.com/eddiethedean/poldantic/blob/main/examples/05_etl_pipeline.ipynb) - Real-world ETL pipeline example

### 🔄 Pydantic ➜ Polars

```python
from pydantic import BaseModel
from poldantic.infer_polars import to_polars_schema
from typing import Optional, List

class Person(BaseModel):
    name: str
    tags: Optional[List[str]]

schema = to_polars_schema(Person)
print(schema)
# {'name': String, 'tags': List(String)}
```

**Initialize a DataFrame with the schema:**

```python
import polars as pl

data = [{"name": "Alice", "tags": ["x"]}, {"name": "Bob", "tags": None}]
df = pl.DataFrame(data, schema=schema)
```

---

### 🔄 Polars ➜ Pydantic

```python
import polars as pl
from poldantic.infer_pydantic import to_pydantic_model

schema = {
    "name": pl.String,
    "tags": pl.List(pl.String())
}

Model = to_pydantic_model(schema)  # fields are Optional[...] by default
print(Model(name="Alice", tags=["x", "y"]))
# name='Alice' tags=['x', 'y']
```

> Pass `force_optional=False` to require fields on the generated model:
>
> ```python
> StrictModel = to_pydantic_model(schema, "StrictModel", force_optional=False)
> ```

---

### 🧬 Nested Models

```python
from pydantic import BaseModel
from poldantic.infer_polars import to_polars_schema

class Address(BaseModel):
    street: str
    zip: int

class Customer(BaseModel):
    id: int
    address: Address

print(to_polars_schema(Customer))
# {'id': Int64, 'address': Struct({'street': String, 'zip': Int64})}
```

---

### ⚡ FastAPI Integration

```python
from fastapi import FastAPI
from pydantic import BaseModel
import polars as pl
from poldantic.infer_polars import to_polars_schema
from poldantic.infer_pydantic import to_pydantic_model

class User(BaseModel):
    id: int
    name: str

schema = to_polars_schema(User)
UserOut = to_pydantic_model(schema, "UserOut", force_optional=False)

app = FastAPI()

@app.get("/users", response_model=list[UserOut])
def list_users():
    df = pl.DataFrame([{"id": 1, "name": "Ada"}, {"id": 2, "name": "Alan"}], schema=schema)
    return df.to_dicts()
```

---

## ⚙️ Settings

Both directions expose thread-safe, context-aware settings you can customize.

### Pydantic ➜ Polars (`poldantic.infer_polars`)

```python
from poldantic.infer_polars import settings, Settings, set_settings

# Modify global settings (backward compatible)
settings.use_pl_enum_for_string_enums = True
settings.decimal_precision = 38
settings.decimal_scale = 18
settings.uuid_as_string = True

# Or use immutable, context-aware settings (recommended for concurrent code)
from poldantic.infer_polars import Settings, set_settings, get_settings

custom_settings = Settings(
    use_pl_enum_for_string_enums=False,
    decimal_precision=10,
    decimal_scale=2,
    uuid_as_string=False
)
set_settings(custom_settings)  # Thread-safe, context-local
```

### Polars ➜ Pydantic (`poldantic.infer_pydantic`)

```python
from poldantic.infer_pydantic import settings

# Map pl.Duration → datetime.timedelta (True) or int (False)
settings.durations_as_timedelta = True

# Default Decimal instance for reverse mapping (precision/scale)
settings.decimal_precision = 38
settings.decimal_scale = 18
```

> **Thread Safety:** Settings use `contextvars` for safe concurrent access. Each context (thread/async task) can have its own settings without interference.

---

## 🛡️ Error Handling

Poldantic provides custom exceptions for better error messages:

```python
from poldantic import (
    PoldanticError,           # Base exception
    SchemaConversionError,    # Schema conversion failures
    UnsupportedTypeError,     # Unsupported type encountered
    InvalidSchemaError,       # Invalid schema provided
)

try:
    schema = to_polars_schema(MyModel)
except SchemaConversionError as e:
    print(f"Conversion failed: {e}")
    print(f"Field: {e.field_name}, Type: {e.field_type}")
```

---

## 📚 Supported Type Mappings

| Python / Pydantic        | ➜ Polars dtype       | ➜ back to Python        |
|--------------------------|----------------------|-------------------------|
| `int`                    | `pl.Int64()`         | `int`                   |
| `float`                  | `pl.Float64()`       | `float`                 |
| `str`                    | `pl.String()`        | `str`                   |
| `bool`                   | `pl.Boolean()`       | `bool`                  |
| `bytes`                  | `pl.Binary()`        | `bytes`                 |
| `datetime.date`          | `pl.Date()`          | `datetime.date`         |
| `datetime.datetime`      | `pl.Datetime()`      | `datetime.datetime`     |
| `datetime.time`          | `pl.Time()`          | `datetime.time`         |
| `datetime.timedelta`     | `pl.Duration()`      | `datetime.timedelta`    |
| `Decimal`                | `pl.Decimal(p,s)`    | `Decimal`               |
| `Enum[str]`              | `pl.Enum([...])` or `pl.String()` | `str`     |
| `list[T]`, `set[T]`      | `pl.List(inner)`     | `list[T]`               |
| `tuple[T, ...]`          | `pl.List(inner)`     | `list[T]`               |
| nested `BaseModel`       | `pl.Struct([...])`   | nested Pydantic model   |
| `Union[int, str]`, `Any` | `pl.Object()`        | `Any`                   |
| `dict[...]`              | `pl.Object()`        | `Any`                   |

> Ambiguous unions (e.g., `Union[int, str]`) intentionally map to `pl.Object()` and back to `typing.Any`.

---

## 🧭 Design Notes

- **Nullability**: From-Polars conversion wraps all fields in `Optional[...]` by default; disable with `force_optional=False`.
- **Utf8 vs String**: Normalized to `pl.String` for forward compatibility.
- **Structs**: Works with tuple fields `("name", dtype)` and `polars.Field` objects.
- **Classes vs Instances**: Accepts both `pl.Int64` and `pl.Int64()` in schema dicts.

---

## 🧪 Development & Testing

### Quick Start

```bash
# Clone the repository
git clone https://github.com/eddiethedean/poldantic.git
cd poldantic

# Install with development dependencies
pip install -e ".[dev,test]"

# Run tests
pytest

# Run with coverage
pytest --cov=poldantic --cov-report=html

# Type checking
mypy poldantic

# Linting & formatting
ruff check poldantic tests
ruff format poldantic tests
```

### Using Make

```bash
make install    # Install all dependencies
make test       # Run tests with coverage
make lint       # Run linters
make format     # Format code
make check      # Run all checks (lint + type check + tests)
```

For more details, see [CONTRIBUTING.md](https://github.com/eddiethedean/poldantic/blob/main/CONTRIBUTING.md).

---

## 💡 When to use Poldantic

- ✅ You already have **Pydantic models** and want to create Polars DataFrames with matching schemas
- ✅ You have **Polars transformations** and need FastAPI response models without manual typing
- ✅ You want **type-safe ETL**: validate with Pydantic → transform with Polars → publish validated results
- ✅ You need **bidirectional schema conversion** between validation and computation layers
- ✅ You're building **data pipelines** that benefit from both Pydantic's validation and Polars' performance

---

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](https://github.com/eddiethedean/poldantic/blob/main/CONTRIBUTING.md) for development setup, coding standards, and submission guidelines.

---

## 📝 Changelog

See [CHANGELOG.md](https://github.com/eddiethedean/poldantic/blob/main/CHANGELOG.md) for a detailed history of changes.

---

## 📄 License

MIT © 2025 Odos Matthews

---

## 🔗 Links

- **PyPI**: https://pypi.org/project/poldantic/
- **GitHub**: https://github.com/eddiethedean/poldantic
- **Issues**: https://github.com/eddiethedean/poldantic/issues
- **Pydantic**: https://docs.pydantic.dev/
- **Polars**: https://pola.rs/
