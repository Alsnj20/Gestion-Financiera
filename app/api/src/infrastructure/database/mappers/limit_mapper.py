"""Shim de compatibilidad — la fuente vive en el módulo limits."""
from __future__ import annotations

from modules.limits.infrastructure.mappers.limit_mapper import to_domain, to_model

__all__ = ["to_domain", "to_model"]
