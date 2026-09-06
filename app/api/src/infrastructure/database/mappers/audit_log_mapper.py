from __future__ import annotations

import uuid
from infrastructure.database.models import AuditLogModel
from modules.audit_logs.domain.entities.audit_log import AuditLog


def to_domain(model: AuditLogModel) -> AuditLog:
    return AuditLog(
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
    return AuditLogModel(
        id=uuid.UUID(domain.id) if _is_uuid(domain.id) else uuid.uuid4(),
        user_id=uuid.UUID(domain.user_id) if _is_uuid(domain.user_id) else uuid.uuid4(),
        entity_type=domain.entity_type,
        entity_id=domain.entity_id,
        action=domain.action,
        old_value=domain.old_value,
        new_value=domain.new_value,
        source=domain.source,
        created_at=domain.created_at,
    )


def _is_uuid(value: str) -> bool:
    try:
        uuid.UUID(str(value))
        return True
    except Exception:
        return False
