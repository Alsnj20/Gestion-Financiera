"""Shim de compatibilidad — la fuente vive en el módulo accounts."""

from __future__ import annotations

from modules.accounts.infrastructure.mappers.account_mapper import to_domain, to_model

__all__ = ["to_domain", "to_model"]
