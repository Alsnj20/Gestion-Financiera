"""Shim de compatibilidad — la fuente vive en el módulo audit_logs."""
from __future__ import annotations

from modules.audit_logs.infrastructure.mappers.audit_log_mapper import to_domain, to_model

__all__ = ["to_domain", "to_model"]
