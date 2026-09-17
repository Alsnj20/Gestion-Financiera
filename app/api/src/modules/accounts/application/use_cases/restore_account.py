from __future__ import annotations

from dataclasses import dataclass

from modules.accounts.application.dtos import RestoreAccountOutput, to_account_output
from modules.accounts.application.ports.account_repository import (
    AccountRepositoryPort,
)
from shared.domain.guards import shadow_original_name
from shared.errors import BusinessRuleError, ConflictError, NotFoundError
from shared.types.enums import AccountStatus


@dataclass(frozen=True, slots=True)
class RestoreAccountInput:
    account_id: str
    user_id: str


class RestoreAccountUseCase:
    def __init__(self, account_repo: AccountRepositoryPort) -> None:
        self._account_repo = account_repo

    async def execute(self, inp: RestoreAccountInput) -> RestoreAccountOutput:
        account = await self._account_repo.find_by_id(inp.account_id)

        if account is None:
            raise NotFoundError(
                code="ACCOUNT_NOT_FOUND",
                message="Cuenta no encontrada",
            )

        # Solo el dueño restaura.
        if account.user_id != inp.user_id:
            raise BusinessRuleError(
                code="FORBIDDEN",
                message="No autorizado",
            )

        if account.status != AccountStatus.ARCHIVED:
            raise BusinessRuleError(
                code="ACCOUNT_NOT_ARCHIVED",
                message="Solo se puede restaurar una cuenta archivada.",
            )

        original = shadow_original_name(account.name)
        if await self._account_repo.exists_name_for_user(inp.user_id, original):
            raise ConflictError(
                code="ACCOUNT_NAME_TAKEN",
                message=f"Ya existe una cuenta activa con el nombre: {original}",
            )

        account = account.restore(original)
        await self._account_repo.save(account)

        return to_account_output(account)
