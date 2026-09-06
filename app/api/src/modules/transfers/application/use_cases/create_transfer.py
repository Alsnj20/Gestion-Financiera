from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
from modules.transfers.domain.entities.transfer import Transfer
from modules.transfers.application.ports.transfer_repository import TransferRepositoryPort
from modules.transactions.application.ports.transaction_repository import TransactionRepositoryPort
from modules.accounts.application.ports.account_repository import AccountRepositoryPort
from modules.transactions.domain.entities.transaction import Transaction
from shared.errors import BusinessRuleError, ValidationError


@dataclass(frozen=True, slots=True)
class CreateTransferInput:
    user_id: str
    source_account_id: str
    destination_account_id: str
    amount: Decimal
    currency: str = "PEN"
    description: str = ""
    date: datetime | None = None


@dataclass(frozen=True, slots=True)
class CreateTransferOutput:
    id: str
    user_id: str
    source_account_id: str
    destination_account_id: str
    amount: Decimal
    currency: str


class CreateTransferUseCase:
    def __init__(
        self,
        transfer_repo: TransferRepositoryPort,
        tx_repo: TransactionRepositoryPort,
        account_repo: AccountRepositoryPort,
    ) -> None:
        self._transfer_repo = transfer_repo
        self._tx_repo = tx_repo
        self._account_repo = account_repo

    async def execute(self, inp: CreateTransferInput) -> CreateTransferOutput:
        # Validar cuentas origen y destino
        source_account = await self._account_repo.find_by_id(inp.source_account_id)
        if not source_account:
            raise ValidationError(code="ACCOUNT_NOT_FOUND", message="Cuenta origen no encontrada")

        dest_account = await self._account_repo.find_by_id(inp.destination_account_id)
        if not dest_account:
            raise ValidationError(code="ACCOUNT_NOT_FOUND", message="Cuenta destino no encontrada")

        # Validar moneda
        if inp.currency and inp.currency != source_account.currency:
            raise BusinessRuleError(code="CURRENCY_MISMATCH", message="Moneda no coincide con cuenta origen")

        # Crear transacción de salida
        tx_out = Transaction.create_expense(
            user_id=inp.user_id, account_id=inp.source_account_id,
            amount=inp.amount, currency=source_account.currency,
            description=f"Transferencia a {dest_account.name}",
        )
        await self._tx_repo.save(tx_out)

        # Crear transacción de entrada
        tx_in = Transaction.create_income(
            user_id=inp.user_id, account_id=inp.destination_account_id,
            amount=inp.amount, currency=dest_account.currency,
            description=f"Transferencia desde {source_account.name}",
        )
        await self._tx_repo.save(tx_in)

        # Crear transferencia
        transfer = Transfer.create(
            user_id=inp.user_id,
            source_account_id=inp.source_account_id,
            destination_account_id=inp.destination_account_id,
            source_transaction_id=tx_out.id,
            destination_transaction_id=tx_in.id,
            amount=inp.amount, currency=source_account.currency,
            description=inp.description, date=inp.date,
        )
        await self._transfer_repo.save(transfer)

        return CreateTransferOutput(
            id=transfer.id, user_id=transfer.user_id,
            source_account_id=transfer.source_account_id,
            destination_account_id=transfer.destination_account_id,
            amount=transfer.amount, currency=transfer.currency,
        )
