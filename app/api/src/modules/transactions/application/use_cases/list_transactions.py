from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from modules.transactions.application.dtos import (
    ListTransactionsOutput,
    to_transaction_output,
)
from modules.transactions.application.ports.transaction_repository import (
    TransactionRepositoryPort,
)
from shared.errors import BusinessRuleError


@dataclass(frozen=True, slots=True)
class ListTransactionsInput:
    user_id: str
    requester_id: str
    requester_role: str = "USER"
    from_date: datetime | None = None
    to_date: datetime | None = None
    account_id: str | None = None
    type: str | None = None


class ListTransactionsUseCase:
    """Orquesta la lógica para listar transacciones de un usuario."""

    def __init__(self, tx_repo: TransactionRepositoryPort) -> None:
        self._tx_repo = tx_repo

    async def execute(self, inp: ListTransactionsInput) -> list[ListTransactionsOutput]:
        # Lectura: dueño o admin.
        if inp.user_id != inp.requester_id and inp.requester_role != "ADMIN":
            raise BusinessRuleError(
                code="FORBIDDEN",
                message="No autorizado",
            )

        transactions = await self._tx_repo.list_by_user(
            inp.user_id,
            from_date=inp.from_date,
            to_date=inp.to_date,
            account_id=inp.account_id,
            type=inp.type,
        )
        return [to_transaction_output(tx) for tx in transactions]
