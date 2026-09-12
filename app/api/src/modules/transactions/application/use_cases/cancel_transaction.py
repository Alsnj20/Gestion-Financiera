from __future__ import annotations

from dataclasses import dataclass

from modules.accounts.application.ports.account_repository import AccountRepositoryPort
from modules.transactions.application.dtos import (
    CancelTransactionOutput,
    to_transaction_output,
)
from modules.transactions.application.ports.transaction_repository import (
    TransactionRepositoryPort,
)
from shared.errors import BusinessRuleError, NotFoundError, ValidationError
from shared.types.enums import TransactionStatus


@dataclass(frozen=True, slots=True)
class CancelTransactionInput:
    tx_id: str
    requester_id: str
    requester_role: str = "USER"


class CancelTransactionUseCase:
    """Cancela revirtiendo el efecto en el balance. Idempotente."""

    def __init__(
        self, tx_repo: TransactionRepositoryPort, account_repo: AccountRepositoryPort
    ) -> None:
        self._tx_repo = tx_repo
        self._account_repo = account_repo

    async def execute(self, inp: CancelTransactionInput) -> CancelTransactionOutput:
        # Lock de la fila: mientras se procesa la cancelación nadie más
        # puede modificar este registro simultáneamente.
        tx = await self._tx_repo.find_by_id(inp.tx_id, for_update=True)

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

        if tx.is_transfer_leg():
            raise ValidationError(
                code="TX_TRANSFER_LEG",
                message="Pata de transferencia: opera vía el agregado Transfer.",
            )

        if tx.status == TransactionStatus.CANCELLED:
            return to_transaction_output(tx)

        account = await self._account_repo.find_by_id(tx.account_id, for_update=True)
        if account is None:
            raise ValidationError(
                code="ACCOUNT_NOT_FOUND", message="Cuenta no encontrada"
            )

        if tx.is_income():
            updated_account = account.apply_expense(tx.amount)
        else:
            updated_account = account.apply_income(tx.amount)

        cancelled = tx.cancel()
        await self._account_repo.save(updated_account)
        await self._tx_repo.save(cancelled)

        return to_transaction_output(cancelled)
