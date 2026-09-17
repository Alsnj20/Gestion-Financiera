"""Shim de compatibilidad — la fuente vive en el módulo tags."""
from __future__ import annotations

from modules.tags.infrastructure.mappers.tag_mapper import to_domain, to_model

__all__ = ["to_domain", "to_model"]
