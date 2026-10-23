"""Shared input checks that raise clear errors for invalid values."""


def require_text(field_name: str, value: object) -> None:
    """Raise an error unless value is a non-blank string."""
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be text, got {value!r}")
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")


def require_positive_number(field_name: str, value: object) -> None:
    """Raise an error unless value is a number greater than zero."""
    if not isinstance(value, int | float):
        raise TypeError(f"{field_name} must be a number, got {value!r}")
    if value <= 0:
        raise ValueError(f"{field_name} must be greater than 0, got {value}")
