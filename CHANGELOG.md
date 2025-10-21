# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2025-10-21

### Added
- **Thread-safe settings** using `contextvars` for concurrent environments
  - New `get_settings()` and `set_settings()` functions
  - Immutable `Settings` dataclass with `.copy()` method
  - Backward-compatible `settings` proxy object
- **Custom exception classes** for better error messages:
  - `PoldanticError` (base exception)
  - `SchemaConversionError` (schema conversion failures)
  - `UnsupportedTypeError` (unsupported type encountered)
  - `InvalidSchemaError` (invalid schema provided)
- **MIT License** file
- **Comprehensive documentation**:
  - `CONTRIBUTING.md` with development guidelines
  - `CHANGELOG.md` for tracking changes
  - Badges in README (PyPI, Python versions, tests, codecov, license)
- **Development tooling**:
  - Pre-commit hooks configuration (`.pre-commit-config.yaml`)
  - Ruff configuration for linting and formatting
  - MyPy configuration for type checking
  - Makefile for common development tasks
  - Pytest, coverage, and tool configurations in `pyproject.toml`
- **CI/CD automation**:
  - GitHub Actions workflow for testing on Python 3.8-3.13
  - GitHub Actions workflow for automated PyPI publishing
  - Dependabot configuration for dependency updates
- **Example notebooks** with executed outputs:
  - `01_basic_usage.ipynb` - Core functionality
  - `02_advanced_types.ipynb` - Nested models, enums, complex types
  - `03_settings_configuration.ipynb` - Settings customization
  - `04_fastapi_integration.ipynb` - FastAPI integration
  - `05_etl_pipeline.ipynb` - Real-world ETL pipeline
  - `examples/README.md` - Guide to all examples
- **Project structure**:
  - Comprehensive `.gitignore` for Python projects
  - PEP 561 compliance with `py.typed` marker
  - Development and test dependencies in `pyproject.toml`
  - `typing-extensions` dependency for Python 3.8 compatibility

### Changed
- **Python 3.8 compatibility ensured** throughout codebase
  - Replaced Python 3.10+ union syntax (`|`) with `Union`
  - Conditional import of `Annotated` from `typing_extensions` for Python 3.8
  - Version-aware handling of `types.UnionType` (Python 3.10+)
  - Version-aware `@dataclass(slots=True)` (Python 3.10+) vs `@dataclass()` (Python 3.8-3.9)
- **Polars Struct handling** now uses `pl.Field` objects instead of tuples
  - Fixes repr() issues with nested models
  - Enables proper DataFrame creation with nested structures
- **Updated all test assertions** from `pl.Utf8()` to `pl.String()`
- **UUID and Decimal handling** now dynamic based on current settings
- **Enhanced README** with:
  - Quick start example
  - Error handling documentation
  - Development & testing guide
  - Links to example notebooks
  - More detailed use cases

### Fixed
- Python version requirement in README now correctly states `>=3.8`
- Test failures due to missing `email-validator` package (now optional test dependency)
- Deprecated Polars `Utf8` type usage in tests
- UUID settings now properly dynamic (respects runtime changes)
- Settings changes now thread-safe and context-aware

### Removed
- Unused `types.py` module and `FieldInfo` class
- Duplicate test files (`test_core.py`, `test_edge.py`)

## [0.2.2] - 2024

### Previous releases
See git history for changes in versions 0.2.2 and earlier.

[Unreleased]: https://github.com/eddiethedean/poldantic/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/eddiethedean/poldantic/compare/v0.2.2...v0.3.0
[0.2.2]: https://github.com/eddiethedean/poldantic/releases/tag/v0.2.2

