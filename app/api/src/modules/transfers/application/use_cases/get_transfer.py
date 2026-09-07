from __future__ import annotations

from dataclasses import dataclass

from modules.transfers.application.dtos import GetTransferOutput, to_transfer_output
from modules.transfers.application.ports.transfer_repository import (
    TransferRepositoryPort,
)
from shared.errors import BusinessRuleError, NotFoundError


@dataclass(frozen=True, slots=True)
class GetTransferInput:
    transfer_id: str
    requester_id: str
    requester_role: str = "USER"


class GetTransferUseCase:
    def __init__(self, transfer_repo: TransferRepositoryPort) -> None:
        self._transfer_repo = transfer_repo

    async def execute(self, inp: GetTransferInput) -> GetTransferOutput:
        transfer = await self._transfer_repo.find_by_id(inp.transfer_id)

        if transfer is None:
            raise NotFoundError(
                code="TRANSFER_NOT_FOUND",
                message="Transferencia no encontrada",
            )

        # Lectura: dueño o admin.
        if transfer.user_id != inp.requester_id and inp.requester_role != "ADMIN":
            raise BusinessRuleError(
                code="FORBIDDEN",
                message="No autorizado",
            )

        return to_transfer_output(transfer)
