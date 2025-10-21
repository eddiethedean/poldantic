.PHONY: help install test lint format check clean build publish

help:
	@echo "Available commands:"
	@echo "  make install    - Install package in development mode with all dependencies"
	@echo "  make test       - Run tests with pytest"
	@echo "  make lint       - Run linters (ruff)"
	@echo "  make format     - Format code with ruff"
	@echo "  make typecheck  - Run type checking with mypy"
	@echo "  make check      - Run all checks (lint + typecheck + test)"
	@echo "  make clean      - Remove build artifacts and caches"
	@echo "  make build      - Build distribution packages"
	@echo "  make publish    - Publish package to PyPI (requires credentials)"

install:
	pip install -e ".[dev,test]"

test:
	pytest tests/ -v --cov=poldantic --cov-report=html --cov-report=term

test-fast:
	pytest tests/ -x

lint:
	ruff check poldantic tests

format:
	ruff format poldantic tests
	ruff check --fix poldantic tests

typecheck:
	mypy poldantic

check: lint typecheck test

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean
	python -m build

publish: build
	twine check dist/*
	twine upload dist/*

dev-setup: install
	pre-commit install
	@echo "Development environment ready!"

