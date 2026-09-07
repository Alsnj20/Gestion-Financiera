from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from modules.accounts.application.ports.account_repository import AccountRepositoryPort
from modules.transactions.application.dtos import (
    CreateTransactionOutput,
    to_transaction_output,
)
from modules.transactions.application.ports.transaction_repository import (
    TransactionRepositoryPort,
)
from modules.transactions.domain.entities.transaction import Transaction
from shared.errors import BusinessRuleError, ValidationError


@dataclass(frozen=True, slots=True)
class CreateTransactionInput:
    """DTO puro de Python sin acoplamiento a Pydantic ni HTTP."""

    user_id: str
    account_id: str
    type: str  # "INCOME" o "EXPENSE"
    amount: Decimal
    currency: str = "PEN"
    description: str = ""
    category_id: str = ""
    payment_method_id: str = ""
    source: str = "MANUAL"
    transaction_date: datetime | None = None


class CreateTransactionUseCase:
    """Orquesta la lógica del caso de uso. Sin dependencias de frameworks."""

    def __init__(
        self, tx_repo: TransactionRepositoryPort, account_repo: AccountRepositoryPort
    ) -> None:
        self._tx_repo = tx_repo
        self._account_repo = account_repo

    async def execute(self, inp: CreateTransactionInput) -> CreateTransactionOutput:
        # 1. Obtener y validar cuenta (bloqueada: el balance se actualiza abajo).
        account = await self._account_repo.find_by_id(inp.account_id, for_update=True)
        if not account:
            raise ValidationError(
                code="ACCOUNT_NOT_FOUND", message="Cuenta no encontrada"
            )

        if account.user_id != inp.user_id:
            raise BusinessRuleError(
                code="FORBIDDEN", message="La cuenta no pertenece al usuario"
            )

        # 2. Crear transacción (tipo explícito: TRANSFER u otro no se cuela como gasto).
        tx_type = inp.type.upper()
        if tx_type == "INCOME":
            tx = Transaction.create_income(
                user_id=inp.user_id,
                account_id=inp.account_id,
                amount=inp.amount,
                currency=inp.currency,
                description=inp.description,
                category_id=inp.category_id,
                payment_method_id=inp.payment_method_id,
                source=inp.source,
                transaction_date=inp.transaction_date,
            )
            # 3. Actualizar balance de cuenta
            updated_account = account.apply_income(inp.amount)
        elif tx_type == "EXPENSE":
            tx = Transaction.create_expense(
                user_id=inp.user_id,
                account_id=inp.account_id,
                amount=inp.amount,
                currency=inp.currency,
                description=inp.description,
                category_id=inp.category_id,
                payment_method_id=inp.payment_method_id,
                source=inp.source,
                transaction_date=inp.transaction_date,
            )
            # 3. Actualizar balance de cuenta
            updated_account = account.apply_expense(inp.amount)
        else:
            raise ValidationError(
                code="TX_TYPE_INVALID",
                message=f"Tipo debe ser INCOME o EXPENSE, recibido: {inp.type}",
            )

        # 4. Persistir cambios
        await self._tx_repo.save(tx)
        await self._account_repo.save(updated_account)

        # 5. Retorno del DTO de salida
        return to_transaction_output(tx)
