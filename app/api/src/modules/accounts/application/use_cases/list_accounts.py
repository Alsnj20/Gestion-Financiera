from __future__ import annotations

from dataclasses import dataclass

from modules.accounts.application.dtos import (
    ListAccountsByUserOutput,
    to_account_output,
)
from modules.accounts.application.ports.account_repository import AccountRepositoryPort
from shared.errors import BusinessRuleError
from shared.types.enums import AccountStatus


@dataclass(frozen=True, slots=True)
class ListAccountsByUserInput:
    user_id: str
    requester_id: str
    requester_role: str = "USER"
    include_archived: bool = False


class ListAccountsByUserUseCase:
    def __init__(self, account_repo: AccountRepositoryPort) -> None:
        self._account_repo = account_repo

    async def execute(
        self, inp: ListAccountsByUserInput
    ) -> list[ListAccountsByUserOutput]:
        # Lectura: dueño o admin. El ownership se valida aquí,
        # no solo en el guard del router.
        if inp.user_id != inp.requester_id and inp.requester_role != "ADMIN":
            raise BusinessRuleError(
                code="FORBIDDEN",
                message="No autorizado",
            )

        accounts = await self._account_repo.find_by_user(inp.user_id)
        if not inp.include_archived:
            accounts = [a for a in accounts if a.status == AccountStatus.ACTIVE]
        return [to_account_output(a) for a in accounts]
