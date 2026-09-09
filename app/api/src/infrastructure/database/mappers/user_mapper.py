"""Shim de compatibilidad — la fuente vive en el módulo users."""
from __future__ import annotations

from modules.users.infrastructure.mappers.user_mapper import to_domain, to_model, update_model

__all__ = ["to_domain", "to_model", "update_model"]
