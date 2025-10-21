# Poldantic Examples

This directory contains interactive Jupyter notebooks demonstrating Poldantic features and use cases.

## 📚 Comprehensive Tutorial Series

Follow these notebooks in order for a complete understanding:

### 1. [01_basic_usage.ipynb](01_basic_usage.ipynb) ⭐ **Start Here**
- Core Pydantic ➜ Polars conversion
- Core Polars ➜ Pydantic conversion
- Working with DataFrames
- Handling optional fields
- Round-trip conversions

### 2. [02_advanced_types.ipynb](02_advanced_types.ipynb)
- Nested Pydantic models → Polars Structs
- Enums and categorical data
- Lists of primitives and complex types
- Lists of nested models

### 3. [03_settings_configuration.ipynb](03_settings_configuration.ipynb)
- Default settings overview
- Modifying settings (backward compatible)
- Thread-safe context-aware settings
- Enum handling configuration
- Decimal precision/scale customization

### 4. [04_fastapi_integration.ipynb](04_fastapi_integration.ipynb)
- Using Poldantic with FastAPI
- Input validation with Pydantic
- Data processing with Polars
- Response model generation
- Complete API workflow

### 5. [05_etl_pipeline.ipynb](05_etl_pipeline.ipynb)
- Real-world ETL example
- Extract: Validate input data
- Transform: Process with Polars
- Load: Validate output
- Type-safe data pipeline

## 📁 Additional Examples

### [poldantic_example.ipynb](poldantic_example.ipynb)
Original example showing basic conversions.

### [poldantic_optionals_example.ipynb](poldantic_optionals_example.ipynb)
Detailed example of handling optional and nullable fields.

## 🚀 Running the Notebooks

### Option 1: Jupyter
```bash
pip install jupyter
jupyter notebook examples/
```

### Option 2: JupyterLab
```bash
pip install jupyterlab
jupyter lab examples/
```

### Option 3: VS Code
Open notebooks directly in VS Code with the Jupyter extension.

## ✅ All Examples Tested

All notebooks in this directory have been tested and verified to run without errors.

## 💡 Tips

- Run cells in order from top to bottom
- Each notebook is self-contained
- Examples use realistic data patterns
- All code is Python 3.8+ compatible

