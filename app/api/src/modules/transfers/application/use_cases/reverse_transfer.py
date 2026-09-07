from __future__ import annotations

from dataclasses import dataclass

from modules.accounts.application.ports.account_repository import AccountRepositoryPort
from modules.transactions.application.ports.transaction_repository import (
    TransactionRepositoryPort,
)
from modules.transfers.application.dtos import ReverseTransferOutput, to_transfer_output
from modules.transfers.application.ports.transfer_repository import (
    TransferRepositoryPort,
)
from shared.errors import BusinessRuleError, NotFoundError, ValidationError
from shared.types.enums import TransactionStatus


@dataclass(frozen=True, slots=True)
class ReverseTransferInput:
    transfer_id: str
    requester_id: str
    requester_role: str = "USER"


class ReverseTransferUseCase:
    """Revierte una transferencia: deshace el movimiento en ambas cuentas,
    marca las patas como CANCELLED y el agregado como REVERSED.

    Nada se borra físicamente: ni el Transfer ni las patas.
    Todo ocurre en una única transacción DB (commit/rollback en el controller).
    """

    def __init__(
        self,
        transfer_repo: TransferRepositoryPort,
        tx_repo: TransactionRepositoryPort,
        account_repo: AccountRepositoryPort,
    ) -> None:
        self._transfer_repo = transfer_repo
        self._tx_repo = tx_repo
        self._account_repo = account_repo

    async def execute(self, inp: ReverseTransferInput) -> ReverseTransferOutput:
        # Lock del agregado: mientras se procesa esta reversión nadie más
        # puede modificar este registro simultáneamente.
        transfer = await self._transfer_repo.find_by_id(
            inp.transfer_id, for_update=True
        )

        if transfer is None:
            raise NotFoundError(
                code="TRANSFER_NOT_FOUND",
                message="Transferencia no encontrada",
            )

        # Escritura: solo el dueño (admin solo lee el ledger ajeno).
        if transfer.user_id != inp.requester_id:
            raise BusinessRuleError(
                code="FORBIDDEN",
                message="No autorizado",
            )

        if transfer.is_reversed():
            # Idempotente: retry seguro (frontend/WhatsApp/backend).
            # Retorna la representación actual sin re-ejecutar nada: ni lecturas
            # de patas/cuentas ni escrituras.
            return to_transfer_output(transfer)

        leg_out = await self._tx_repo.find_by_id(
            transfer.source_transaction_id, for_update=True
        )
        leg_in = await self._tx_repo.find_by_id(
            transfer.destination_transaction_id, for_update=True
        )
        if leg_out is None or leg_in is None:
            raise ValidationError(
                code="TR_LEGS_MISSING",
                message="Patas de la transferencia no encontradas",
            )
        if leg_out.status != leg_in.status:
            raise ValidationError(
                code="TR_LEGS_INCONSISTENT",
                message="Patas de la transferencia en estado inconsistente",
            )

        # Cross-check: las patas deben pertenecer a este agregado.
        if (
            leg_out.account_id != transfer.source_account_id
            or leg_in.account_id != transfer.destination_account_id
            or leg_out.amount != transfer.amount
            or leg_in.amount != transfer.amount
        ):
            raise ValidationError(
                code="TR_LEGS_MISMATCH",
                message="Patas no corresponden a la transferencia",
            )

        if leg_out.status == TransactionStatus.CANCELLED:
            # Reversión previa a medias: patas ya revertidas, solo falta el agregado.
            reversed_transfer = transfer.mark_reversed()
            await self._transfer_repo.save(reversed_transfer)
            return to_transfer_output(reversed_transfer)

        # Cuentas bloqueadas en orden determinista (anti-deadlock).
        locked_accounts = {}
        for account_id in sorted(
            {transfer.source_account_id, transfer.destination_account_id}
        ):
            account = await self._account_repo.find_by_id(account_id, for_update=True)
            if account is not None:
                locked_accounts[account_id] = account
        source_account = locked_accounts.get(transfer.source_account_id)
        dest_account = locked_accounts.get(transfer.destination_account_id)
        if source_account is None or dest_account is None:
            raise ValidationError(
                code="ACCOUNT_NOT_FOUND",
                message="Cuenta de la transferencia no encontrada",
            )

        # Deshacer: la salida vuelve como ingreso, la entrada como gasto.
        updated_source = source_account.apply_income(transfer.amount)
        updated_dest = dest_account.apply_expense(transfer.amount)

        await self._account_repo.save(updated_source)
        await self._account_repo.save(updated_dest)
        await self._tx_repo.save(leg_out.mark_leg_reversed())
        await self._tx_repo.save(leg_in.mark_leg_reversed())
        reversed_transfer = transfer.mark_reversed()
        await self._transfer_repo.save(reversed_transfer)

        return to_transfer_output(reversed_transfer)
