"""Shim de compatibilidad — la fuente vive en el módulo debts."""
from __future__ import annotations

from modules.debts.infrastructure.mappers.debt_mapper import to_domain, to_model

__all__ = ["to_domain", "to_model"]
