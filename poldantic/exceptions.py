"""
Custom exceptions for Poldantic.

Provides clear error messages for conversion failures and type mismatches.
"""

from typing import Any, Optional


class PoldanticError(Exception):
    """Base exception for all Poldantic errors."""

    pass


class SchemaConversionError(PoldanticError):
    """Raised when schema conversion fails between Pydantic and Polars."""

    def __init__(
        self, message: str, field_name: Optional[str] = None, field_type: Optional[Any] = None
    ):
        self.field_name = field_name
        self.field_type = field_type
        if field_name:
            message = f"Field '{field_name}': {message}"
        if field_type:
            message = f"{message} (type: {field_type})"
        super().__init__(message)


class UnsupportedTypeError(SchemaConversionError):
    """Raised when an unsupported type is encountered during conversion."""

    def __init__(self, field_type: Any, field_name: Optional[str] = None):
        message = "Unsupported type for conversion"
        super().__init__(message, field_name=field_name, field_type=field_type)


class InvalidSchemaError(PoldanticError):
    """Raised when a schema is invalid or malformed."""

    pass
