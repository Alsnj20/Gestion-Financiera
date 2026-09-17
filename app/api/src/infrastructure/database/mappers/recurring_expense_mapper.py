"""Shim de compatibilidad — la fuente vive en el módulo recurring_expenses."""
from __future__ import annotations

from modules.recurring_expenses.infrastructure.mappers.recurring_expense_mapper import (
    to_domain,
    to_model,
)

__all__ = ["to_domain", "to_model"]
