from __future__ import annotations

from dataclasses import dataclass

from modules.transactions.application.dtos import (
    GetTransactionOutput,
    to_transaction_output,
)
from modules.transactions.application.ports.transaction_repository import (
    TransactionRepositoryPort,
)
from shared.errors import BusinessRuleError, NotFoundError


@dataclass(frozen=True, slots=True)
class GetTransactionInput:
    tx_id: str
    requester_id: str
    requester_role: str = "USER"


class GetTransactionUseCase:
    def __init__(self, tx_repo: TransactionRepositoryPort) -> None:
        self._tx_repo = tx_repo

    async def execute(self, inp: GetTransactionInput) -> GetTransactionOutput:
        tx = await self._tx_repo.find_by_id(inp.tx_id)

        if tx is None:
            raise NotFoundError(
                code="TX_NOT_FOUND",
                message="Transacción no encontrada",
            )

        # Lectura: dueño o admin.
        if tx.user_id != inp.requester_id and inp.requester_role != "ADMIN":
            raise BusinessRuleError(
                code="FORBIDDEN",
                message="No autorizado",
            )

        return to_transaction_output(tx)
