"""Mapper Transfer DB <-> dominio. Vive en el módulo (fuente única).

El mapper global `infrastructure/database/mappers/transfer_mapper.py`
re-exporta desde aquí por compatibilidad.
"""

from __future__ import annotations

import uuid

from infrastructure.database.models import TransferModel
from modules.transfers.domain.entities.transfer import Transfer
from shared.errors import ValidationError
from shared.utils.uuids import is_uuid as _is_uuid


def _req_uuid(value: object, field: str) -> uuid.UUID:
    if not _is_uuid(value):
        raise ValidationError(code="TR_ID_REQUIRED", message=f"{field} inválido")
    return uuid.UUID(str(value))


def to_domain(model: TransferModel) -> Transfer:
    return Transfer.rehydrate(
        id=str(model.id) if model.id else "",
        user_id=str(model.user_id) if model.user_id else "",
        source_account_id=str(model.source_account_id)
        if model.source_account_id
        else "",
        destination_account_id=str(model.destination_account_id)
        if model.destination_account_id
        else "",
        source_transaction_id=str(model.source_transaction_id)
        if model.source_transaction_id
        else "",
        destination_transaction_id=str(model.destination_transaction_id)
        if model.destination_transaction_id
        else "",
        amount=getattr(model, "amount", 0),
        currency=getattr(model, "currency", "PEN"),
        date=getattr(model, "date", None),
        description=getattr(model, "description", ""),
        status=getattr(model, "status", "ACTIVE"),
        created_at=getattr(model, "created_at", None),
        updated_at=getattr(model, "updated_at", None),
    )


def to_model(domain: Transfer) -> TransferModel:
    """Falla en voz alta con ids inválidos: nunca inventa UUIDs al azar."""
    return TransferModel(
        id=_req_uuid(domain.id, "id"),
        user_id=_req_uuid(domain.user_id, "user_id"),
        source_account_id=_req_uuid(domain.source_account_id, "source_account_id"),
        destination_account_id=_req_uuid(
            domain.destination_account_id, "destination_account_id"
        ),
        source_transaction_id=_req_uuid(
            domain.source_transaction_id, "source_transaction_id"
        ),
        destination_transaction_id=_req_uuid(
            domain.destination_transaction_id, "destination_transaction_id"
        ),
        amount=domain.amount,
        currency=domain.currency,
        date=domain.date,
        description=domain.description or "",
        status=domain.status.value
        if hasattr(domain.status, "value")
        else str(domain.status),
        created_at=domain.created_at,
        updated_at=domain.updated_at,
    )
