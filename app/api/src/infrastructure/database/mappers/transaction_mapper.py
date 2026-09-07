"""Shim de compatibilidad — la fuente vive en el módulo transactions."""
from __future__ import annotations

from modules.transactions.infrastructure.mappers.transaction_mapper import to_domain, to_model

__all__ = ["to_domain", "to_model"]
