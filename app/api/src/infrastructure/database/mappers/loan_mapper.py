"""Shim de compatibilidad — la fuente vive en el módulo loans."""
from __future__ import annotations

from modules.loans.infrastructure.mappers.loan_mapper import to_domain, to_model

__all__ = ["to_domain", "to_model"]
