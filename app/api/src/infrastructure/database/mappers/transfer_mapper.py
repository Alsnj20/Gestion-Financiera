from __future__ import annotations

import uuid
from infrastructure.database.models import TransferModel
from modules.transfers.domain.entities.transfer import Transfer


def to_domain(model: TransferModel) -> Transfer:
    return Transfer.rehydrate(
        id=str(model.id) if model.id else "",
        user_id=str(model.user_id) if model.user_id else "",
        source_account_id=str(model.source_account_id) if model.source_account_id else "",
        destination_account_id=str(model.destination_account_id) if model.destination_account_id else "",
        source_transaction_id=str(model.source_transaction_id) if model.source_transaction_id else "",
        destination_transaction_id=str(model.destination_transaction_id) if model.destination_transaction_id else "",
        amount=getattr(model, "amount", 0),
        currency=getattr(model, "currency", "PEN"),
        date=getattr(model, "date", None),
        description=getattr(model, "description", ""),
        created_at=getattr(model, "created_at", None),
    )


def to_model(domain: Transfer) -> TransferModel:
    return TransferModel(
        id=uuid.UUID(domain.id) if _is_uuid(domain.id) else uuid.uuid4(),
        user_id=uuid.UUID(domain.user_id) if _is_uuid(domain.user_id) else uuid.uuid4(),
        source_account_id=uuid.UUID(domain.source_account_id) if _is_uuid(domain.source_account_id) else uuid.uuid4(),
        destination_account_id=uuid.UUID(domain.destination_account_id) if _is_uuid(domain.destination_account_id) else uuid.uuid4(),
        source_transaction_id=uuid.UUID(domain.source_transaction_id) if _is_uuid(domain.source_transaction_id) else uuid.uuid4(),
        destination_transaction_id=uuid.UUID(domain.destination_transaction_id) if _is_uuid(domain.destination_transaction_id) else uuid.uuid4(),
        amount=domain.amount,
        currency=domain.currency,
        date=domain.date,
        description=domain.description or "",
        created_at=domain.created_at,
    )


def _is_uuid(value: str) -> bool:
    try:
        uuid.UUID(str(value))
        return True
    except Exception:
        return False
