from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime

from modules.transactions.domain.entities.transaction import Transaction
from modules.transactions.application.ports.transaction_repository import TransactionRepositoryPort
from modules.accounts.application.ports.account_repository import AccountRepositoryPort
from shared.errors import ValidationError


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


@dataclass(frozen=True, slots=True)
class CreateTransactionOutput:
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


class CreateTransactionUseCase:
    """Orquesta la lógica del caso de uso. Sin dependencias de frameworks."""

    def __init__(self, tx_repo: TransactionRepositoryPort, account_repo: AccountRepositoryPort) -> None:
        self._tx_repo = tx_repo
        self._account_repo = account_repo

    async def execute(self, inp: CreateTransactionInput) -> CreateTransactionOutput:
        # 1. Obtener y validar cuenta
        account = await self._account_repo.find_by_id(inp.account_id)
        if not account:
            raise ValidationError(code="ACCOUNT_NOT_FOUND", message="Cuenta no encontrada")

        if account.user_id != inp.user_id:
            raise ValidationError(code="ACCOUNT_USER_MISMATCH", message="La cuenta no pertenece al usuario")

        # 2. Crear transacción
        if inp.type.upper() == "INCOME":
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
        else:
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

        # 4. Persistir cambios
        await self._tx_repo.save(tx)
        await self._account_repo.save(updated_account)

        # 5. Retorno del DTO de salida
        return CreateTransactionOutput(
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
