"""Mapper Transaction DB <-> dominio. Vive en el módulo (fuente única).

El mapper global `infrastructure/database/mappers/transaction_mapper.py`
re-exporta desde aquí por compatibilidad.
"""

from __future__ import annotations

import uuid

from infrastructure.database.models import TransactionModel
from modules.transactions.domain.entities.transaction import Transaction
from shared.utils.uuids import is_uuid as _is_uuid


def to_domain(model: TransactionModel) -> Transaction:
    return Transaction.rehydrate(
        id=str(model.id) if model.id else "",
        user_id=str(model.user_id) if model.user_id else "",
        account_id=str(model.account_id) if model.account_id else "",
        type=getattr(model, "type", "EXPENSE"),
        amount=getattr(model, "amount", 0),
        currency=getattr(model, "currency", "PEN"),
        transaction_date=getattr(model, "transaction_date", None),
        concepto=getattr(model, "concepto", "") or "",
        category_id=str(model.category_id) if model.category_id else "",
        payment_method_id=str(model.payment_method_id)
        if model.payment_method_id
        else "",
        source=getattr(model, "source", "MANUAL"),
        status=getattr(model, "status", "COMPLETED"),
        created_at=getattr(model, "created_at", None),
        updated_at=getattr(model, "updated_at", None),
    )


def to_model(domain: Transaction) -> TransactionModel:
    """Falla en voz alta con ids inválidos: nunca inventa user/account al azar."""
    if not _is_uuid(domain.id):
        raise ValueError(f"Transaction.id inválido: {domain.id!r}")
    if not _is_uuid(domain.user_id):
        raise ValueError(f"Transaction.user_id inválido: {domain.user_id!r}")
    if not _is_uuid(domain.account_id):
        raise ValueError(f"Transaction.account_id inválido: {domain.account_id!r}")
    return TransactionModel(
        id=uuid.UUID(domain.id),
        user_id=uuid.UUID(domain.user_id),
        account_id=uuid.UUID(domain.account_id),
        payment_method_id=uuid.UUID(domain.payment_method_id)
        if _is_uuid(domain.payment_method_id)
        else None,
        type=domain.type.value if hasattr(domain.type, "value") else str(domain.type),
        amount=domain.amount,
        currency=domain.currency,
        transaction_date=domain.transaction_date,
        concepto=domain.concepto or "",
        category_id=uuid.UUID(domain.category_id)
        if _is_uuid(domain.category_id)
        else None,
        source=domain.source.value
        if hasattr(domain.source, "value")
        else str(domain.source),
        status=domain.status.value
        if hasattr(domain.status, "value")
        else str(domain.status),
        created_at=domain.created_at,
        updated_at=domain.updated_at,
    )
