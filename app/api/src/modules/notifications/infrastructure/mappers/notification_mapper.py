"""Mapper Notification DB <-> dominio. Vive en el módulo (fuente única).

El mapper global `infrastructure/database/mappers/notification_mapper.py`
re-exporta desde aquí por compatibilidad.
"""

from __future__ import annotations

import uuid

from infrastructure.database.models import NotificationModel
from modules.notifications.domain.entities.notification import Notification
from shared.errors import ValidationError
from shared.utils.uuids import is_uuid as _is_uuid


def to_domain(model: NotificationModel) -> Notification:
    return Notification.rehydrate(
        id=str(model.id) if model.id else "",
        user_id=str(model.user_id) if model.user_id else "",
        type=getattr(model, "type", "GENERAL"),
        title=getattr(model, "title", ""),
        message=getattr(model, "message", ""),
        scheduled_at=getattr(model, "scheduled_at", None),
        sent_at=getattr(model, "sent_at", None),
        status=getattr(model, "status", "PENDING"),
        related_entity_type=getattr(model, "related_entity_type", ""),
        related_entity_id=getattr(model, "related_entity_id", ""),
        created_at=getattr(model, "created_at", None),
    )


def to_model(domain: Notification) -> NotificationModel:
    """Falla en voz alta con ids inválidos: nunca inventa UUIDs al azar."""
    if not _is_uuid(domain.id):
        raise ValidationError(code="NOTIF_ID_REQUIRED", message="id requerido")
    if not _is_uuid(domain.user_id):
        raise ValidationError(code="NOTIF_USER_REQUIRED", message="user_id requerido")
    return NotificationModel(
        id=uuid.UUID(domain.id),
        user_id=uuid.UUID(domain.user_id),
        type=domain.type,
        title=domain.title,
        message=domain.message,
        scheduled_at=domain.scheduled_at,
        sent_at=domain.sent_at,
        status=domain.status.value
        if hasattr(domain.status, "value")
        else str(domain.status),
        related_entity_type=domain.related_entity_type,
        related_entity_id=domain.related_entity_id,
        created_at=domain.created_at,
    )
