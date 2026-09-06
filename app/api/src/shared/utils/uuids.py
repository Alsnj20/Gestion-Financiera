"""Helpers UUID compartidos — única fuente de verdad para `_is_uuid`.

Evita las ~15 copias locales en repos/mappers.
"""

from __future__ import annotations

import uuid


def is_uuid(value: object) -> bool:
    try:
        uuid.UUID(str(value))
        return True
    except (ValueError, AttributeError, TypeError):
        return False


def to_uuid_or_none(value: object) -> uuid.UUID | None:
    return uuid.UUID(str(value)) if is_uuid(value) else None


# Alias de compatibilidad para imports antiguos `from x import _is_uuid`.
_is_uuid = is_uuid
