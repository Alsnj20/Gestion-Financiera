"""Guards genéricos de dominio — normalización/validación reutilizable.

Extraído de `modules/accounts/domain/entities/account.py` para que
tags/categories/etc. no dupliquen `_clean_str/_validate_bool`.
"""

from __future__ import annotations

from datetime import UTC, datetime

from shared.errors import ValidationError


def utcnow() -> datetime:
    return datetime.now(UTC)


def clean_str(value: object, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def normalize_name(value: object) -> str:
    """Nombre canónico para comparar unicidad: trim + casefold."""
    return clean_str(value).casefold()


def validate_bool(value: object, field_name: str, prefix: str = "ACCOUNT") -> bool:
    if isinstance(value, bool):
        return value
    raise ValidationError(
        code=f"{prefix}_{field_name.upper()}_INVALID",
        message=f"{field_name} debe ser booleano",
    )


def require_non_empty(value: str, code: str, message: str) -> str:
    if not value:
        raise ValidationError(code=code, message=message)
    return value
