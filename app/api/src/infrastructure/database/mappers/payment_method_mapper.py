"""Shim de compatibilidad — la fuente vive en el módulo payment_methods."""
from __future__ import annotations

from modules.payment_methods.infrastructure.mappers.payment_method_mapper import (
    to_domain,
    to_model,
)

__all__ = ["to_domain", "to_model"]
