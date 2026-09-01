from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime

from modules.transactions.application.ports.transaction_repository import TransactionRepositoryPort


@dataclass(frozen=True, slots=True)
class TransactionOutput:
    """DTO de salida para una transacción."""
    id: str
    user_id: str
    account_id: str
    type: str
    amount: Decimal
    currency: str
    description: str
    category_id: str
    payment_method_id: str
    source: str
    status: str
    transaction_date: datetime


class ListTransactionsUseCase:
    """Orquesta la lógica para listar transacciones de un usuario."""

    def __init__(self, tx_repo: TransactionRepositoryPort) -> None:
        self._tx_repo = tx_repo

    async def execute(
        self,
        user_id: str,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        account_id: str | None = None,
        type: str | None = None,
    ) -> list[TransactionOutput]:
        transactions = await self._tx_repo.list_by_user(
            user_id,
            from_date=from_date,
            to_date=to_date,
            account_id=account_id,
            type=type,
        )
        return [
            TransactionOutput(
                id=tx.id,
                user_id=tx.user_id,
                account_id=tx.account_id,
                type=tx.type.value if hasattr(tx.type, "value") else str(tx.type),
                amount=tx.amount,
                currency=tx.currency,
                description=tx.description,
                category_id=tx.category_id,
                payment_method_id=tx.payment_method_id,
                source=tx.source.value if hasattr(tx.source, "value") else str(tx.source),
                status=tx.status.value if hasattr(tx.status, "value") else str(tx.status),
                transaction_date=tx.transaction_date,
            )
            for tx in transactions
        ]
