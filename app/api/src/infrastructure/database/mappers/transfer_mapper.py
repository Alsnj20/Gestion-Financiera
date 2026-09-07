"""Shim de compatibilidad — la fuente vive en el módulo transfers."""
from __future__ import annotations

from modules.transfers.infrastructure.mappers.transfer_mapper import to_domain, to_model

__all__ = ["to_domain", "to_model"]
