"""Shim de compatibilidad — la fuente vive en el módulo categories."""
from __future__ import annotations

from modules.categories.infrastructure.mappers.category_mapper import to_domain, to_model

__all__ = ["to_domain", "to_model"]
