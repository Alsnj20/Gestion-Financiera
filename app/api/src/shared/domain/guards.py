"""Guards genéricos de dominio — normalización/validación reutilizable.

Extraído de `modules/accounts/domain/entities/account.py` para que
tags/categories/etc. no dupliquen `_clean_str/_validate_bool`.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

from shared.errors import ValidationError


def utcnow() -> datetime:
    return datetime.now(UTC)


def today() -> date:
    return date.today()  # noqa: DTZ011 - date (sin hora) no lleva tz


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


def safe_date(value: object, default: date | None = None) -> date:
    """Fecha defensiva: datetime/str ISO válidos, resto → default o hoy."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value.strip())
        except ValueError:
            pass
    return default or today()
