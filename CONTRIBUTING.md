# Contributing to Poldantic

Thank you for your interest in contributing to Poldantic! This document provides guidelines and instructions for contributing.

## Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/eddiethedean/poldantic.git
   cd poldantic
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install development dependencies**
   ```bash
   pip install -e ".[dev,test]"
   ```

4. **Install pre-commit hooks**
   ```bash
   pre-commit install
   ```

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=poldantic --cov-report=html

# Run specific test file
pytest tests/test_infer_polars.py

# Run tests in parallel
pytest -n auto
```

### Code Quality

```bash
# Format code with ruff
ruff format poldantic tests

# Lint code
ruff check poldantic tests

# Fix auto-fixable issues
ruff check --fix poldantic tests

# Type check
mypy poldantic
```

### Using Make Commands

```bash
make test      # Run tests
make lint      # Run linters
make format    # Format code
make check     # Run all checks (lint + type check + tests)
make clean     # Clean build artifacts
```

## Contributing Guidelines

### Code Style

- Follow PEP 8 guidelines
- Use type hints for all functions
- Write docstrings for public APIs (Google style)
- Keep functions focused and small
- Maximum line length: 100 characters

### Commit Messages

- Use clear, descriptive commit messages
- Start with a verb in present tense (e.g., "Add", "Fix", "Update")
- Reference issue numbers when applicable

### Pull Requests

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write tests for new features
   - Update documentation as needed
   - Ensure all tests pass

3. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```
   - Open a pull request on GitHub
   - Describe your changes clearly
   - Link related issues

### Testing

- Write tests for all new features and bug fixes
- Maintain or improve code coverage
- Test against Python 3.8+ compatibility
- Include both positive and negative test cases

### Documentation

- Update README.md for user-facing changes
- Add docstrings to new functions/classes
- Update CHANGELOG.md with notable changes
- Include examples for new features

## Python Compatibility

Poldantic supports Python 3.8+. Please ensure:
- Use `typing.List`, `typing.Dict`, etc. instead of built-in generics
- Use `Union[X, None]` instead of `X | None` syntax
- Avoid features introduced after Python 3.8

## Release Process

1. Update version in `pyproject.toml` and `poldantic/__init__.py`
2. Update CHANGELOG.md
3. Create a git tag: `git tag v0.x.x`
4. Push tag: `git push origin v0.x.x`
5. Create a GitHub release (triggers PyPI publish)

## Questions?

Feel free to open an issue for questions or discussions!

