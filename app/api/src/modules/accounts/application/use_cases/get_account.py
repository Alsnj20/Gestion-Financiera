from __future__ import annotations

from dataclasses import dataclass

from modules.accounts.application.dtos import GetAccountOutput, to_account_output
from modules.accounts.application.ports.account_repository import AccountRepositoryPort
from shared.errors import BusinessRuleError, NotFoundError


@dataclass(frozen=True, slots=True)
class GetAccountInput:
    account_id: str
    requester_id: str
    requester_role: str = "USER"


class GetAccountUseCase:
    def __init__(self, account_repo: AccountRepositoryPort) -> None:
        self._account_repo = account_repo

    async def execute(self, inp: GetAccountInput) -> GetAccountOutput:
        account = await self._account_repo.find_by_id(inp.account_id)

        if account is None:
            raise NotFoundError(
                code="ACCOUNT_NOT_FOUND",
                message="Cuenta no encontrada",
            )

        # Lectura: dueño o admin (el admin solo observa, no edita).
        if account.user_id != inp.requester_id and inp.requester_role != "ADMIN":
            raise BusinessRuleError(
                code="FORBIDDEN",
                message="No autorizado",
            )

        return to_account_output(account)
