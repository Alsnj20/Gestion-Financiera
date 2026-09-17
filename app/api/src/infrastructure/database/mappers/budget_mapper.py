"""Shim de compatibilidad — la fuente vive en el módulo budgets."""
from __future__ import annotations

from modules.budgets.infrastructure.mappers.budget_mapper import to_domain, to_model

__all__ = ["to_domain", "to_model"]
