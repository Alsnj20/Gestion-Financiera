"""DTOs de salida unificados del módulo audit_logs.

Fuente única: `AuditLogOutput` + `to_audit_log_output`.
"""

from __future__ import annotations

from dataclasses import dataclass

from modules.audit_logs.domain.entities.audit_log import AuditLog


@dataclass(frozen=True, slots=True)
class AuditLogOutput:
    id: str
    user_id: str
    entity_type: str
    entity_id: str
    action: str
    source: str


def to_audit_log_output(log: AuditLog) -> AuditLogOutput:
    return AuditLogOutput(
        id=log.id,
        user_id=log.user_id,
        entity_type=log.entity_type,
        entity_id=log.entity_id,
        action=log.action,
        source=log.source,
    )


# Aliases de compatibilidad.
CreateAuditLogOutput = AuditLogOutput
ListAuditLogsOutput = AuditLogOutput
