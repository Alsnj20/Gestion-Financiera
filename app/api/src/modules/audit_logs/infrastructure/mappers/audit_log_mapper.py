"""Mapper AuditLog DB <-> dominio. Vive en el módulo (fuente única).

El mapper global `infrastructure/database/mappers/audit_log_mapper.py`
re-exporta desde aquí por compatibilidad.
"""

from __future__ import annotations

import uuid

from infrastructure.database.models import AuditLogModel
from modules.audit_logs.domain.entities.audit_log import AuditLog
from shared.errors import ValidationError
from shared.utils.uuids import is_uuid as _is_uuid


def to_domain(model: AuditLogModel) -> AuditLog:
    return AuditLog.rehydrate(
        id=str(model.id) if model.id else "",
        user_id=str(model.user_id) if model.user_id else "",
        entity_type=getattr(model, "entity_type", ""),
        entity_id=getattr(model, "entity_id", ""),
        action=getattr(model, "action", ""),
        old_value=getattr(model, "old_value", None),
        new_value=getattr(model, "new_value", None),
        source=getattr(model, "source", "MANUAL"),
        created_at=getattr(model, "created_at", None),
    )


def to_model(domain: AuditLog) -> AuditLogModel:
    """Falla en voz alta con ids inválidos: nunca inventa UUIDs al azar."""
    if not _is_uuid(domain.id):
        raise ValidationError(code="AL_ID_REQUIRED", message="id requerido")
    if not _is_uuid(domain.user_id):
        raise ValidationError(code="AL_USER_REQUIRED", message="user_id requerido")
    return AuditLogModel(
        id=uuid.UUID(domain.id),
        user_id=uuid.UUID(domain.user_id),
        entity_type=domain.entity_type,
        entity_id=domain.entity_id,
        action=domain.action,
        old_value=domain.old_value,
        new_value=domain.new_value,
        source=domain.source,
        created_at=domain.created_at,
    )
