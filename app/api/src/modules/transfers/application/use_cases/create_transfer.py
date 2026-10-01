from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from modules.accounts.application.ports.account_repository import AccountRepositoryPort
from modules.transactions.application.ports.transaction_repository import (
    TransactionRepositoryPort,
)
from modules.transactions.domain.entities.transaction import Transaction
from modules.transfers.application.dtos import CreateTransferOutput, to_transfer_output
from modules.transfers.application.ports.transfer_repository import (
    TransferRepositoryPort,
)
from modules.transfers.domain.entities.transfer import Transfer
from shared.errors import BusinessRuleError, ValidationError
from shared.types.enums import TransactionSource


@dataclass(frozen=True, slots=True)
class CreateTransferInput:
    user_id: str
    source_account_id: str
    destination_account_id: str
    amount: Decimal
    currency: str = "PEN"
    description: str = ""
    date: datetime | None = None


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
        # 1. Validar cuentas origen y destino (existencia + ownership).
        #    Locks en orden determinista (id ordenado): evita deadlock entre
        #    transferencias concurrentes en direcciones opuestas.
        locked = {}
        for account_id in sorted({inp.source_account_id, inp.destination_account_id}):
            account = await self._account_repo.find_by_id(account_id, for_update=True)
            if account is not None:
                locked[account_id] = account
        source_account = locked.get(inp.source_account_id)
        if not source_account:
            raise ValidationError(
                code="ACCOUNT_NOT_FOUND", message="Cuenta origen no encontrada"
            )

        dest_account = locked.get(inp.destination_account_id)
        if not dest_account:
            raise ValidationError(
                code="ACCOUNT_NOT_FOUND", message="Cuenta destino no encontrada"
            )

        if source_account.user_id != inp.user_id or dest_account.user_id != inp.user_id:
            raise BusinessRuleError(
                code="FORBIDDEN",
                message="Las cuentas no pertenecen al usuario",
            )

        # 2. Validar moneda (origen, destino e input en la misma moneda; sin conversión 1:1).
        if inp.currency and inp.currency != source_account.currency:
            raise BusinessRuleError(
                code="CURRENCY_MISMATCH", message="Moneda no coincide con cuenta origen"
            )
        if dest_account.currency != source_account.currency:
            raise BusinessRuleError(
                code="CURRENCY_MISMATCH",
                message=f"Cuentas en distinta moneda: {source_account.currency} vs {dest_account.currency}",
            )

        # 3. Construir todo en memoria primero (valida monto>0 y misma cuenta
        #    ANTES de persistir nada; antes se guardaba y luego fallaba).
        tx_out = Transaction.create_expense(
            user_id=inp.user_id,
            account_id=inp.source_account_id,
            amount=inp.amount,
            currency=source_account.currency,
            concepto=f"Transferencia a {dest_account.name}",
            source=TransactionSource.TRANSFER,
        )
        tx_in = Transaction.create_income(
            user_id=inp.user_id,
            account_id=inp.destination_account_id,
            amount=inp.amount,
            currency=dest_account.currency,
            concepto=f"Transferencia desde {source_account.name}",
            source=TransactionSource.TRANSFER,
        )
        transfer = Transfer.create(
            user_id=inp.user_id,
            source_account_id=inp.source_account_id,
            destination_account_id=inp.destination_account_id,
            source_transaction_id=tx_out.id,
            destination_transaction_id=tx_in.id,
            amount=inp.amount,
            currency=source_account.currency,
            description=inp.description,
            date=inp.date,
        )

        # 4. Actualizar balances de ambas cuentas.
        updated_source = source_account.apply_expense(inp.amount)
        updated_dest = dest_account.apply_income(inp.amount)

        # 5. Persistir (una sola unidad de trabajo; el commit lo hace el caller).
        await self._tx_repo.save(tx_out)
        await self._tx_repo.save(tx_in)
        await self._account_repo.save(updated_source)
        await self._account_repo.save(updated_dest)
        await self._transfer_repo.save(transfer)

        return to_transfer_output(transfer)
