"""Shim de compatibilidad — la fuente vive en el módulo notifications."""
from __future__ import annotations

from modules.notifications.infrastructure.mappers.notification_mapper import (
    to_domain,
    to_model,
)

__all__ = ["to_domain", "to_model"]
