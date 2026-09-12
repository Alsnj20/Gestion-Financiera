from __future__ import annotations

from dataclasses import dataclass

from modules.transactions.application.dtos import (
    UpdateTransactionOutput,
    to_transaction_output,
)
from modules.transactions.application.ports.transaction_repository import (
    TransactionRepositoryPort,
)
from shared.errors import BusinessRuleError, NotFoundError


@dataclass(frozen=True, slots=True)
class UpdateTransactionInput:
    tx_id: str
    requester_id: str
    requester_role: str = "USER"
    description: str | None = None
    category_id: str | None = None
    payment_method_id: str | None = None


class UpdateTransactionUseCase:
    """Solo metadatos.

    amount/type/account_id son inmutables: cambiarlos sin revertir el balance
    descuadra el ledger. Para corregir un monto se cancela y se recrea.
    """

    def __init__(self, tx_repo: TransactionRepositoryPort) -> None:
        self._tx_repo = tx_repo

    async def execute(self, inp: UpdateTransactionInput) -> UpdateTransactionOutput:
        tx = await self._tx_repo.find_by_id(inp.tx_id)

        if tx is None:
            raise NotFoundError(
                code="TX_NOT_FOUND",
                message="Transacción no encontrada",
            )

        # Escritura: solo el dueño (admin solo lee el ledger ajeno).
        if tx.user_id != inp.requester_id:
            raise BusinessRuleError(
                code="FORBIDDEN",
                message="No autorizado",
            )

        updated = tx.update_metadata(
            description=inp.description,
            category_id=inp.category_id,
            payment_method_id=inp.payment_method_id,
        )

        await self._tx_repo.save(updated)

        return to_transaction_output(updated)
