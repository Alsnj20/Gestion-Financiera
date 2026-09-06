from __future__ import annotations

from dataclasses import dataclass

from modules.accounts.application.dtos import UpdateAccountOutput, to_account_output
from modules.accounts.application.ports.account_repository import (
    AccountRepositoryPort,
)
from shared.errors import (
    BusinessRuleError,
    ConflictError,
    NotFoundError,
)
from shared.types.enums import AccountStatus


@dataclass(frozen=True, slots=True)
class UpdateAccountInput:
    account_id: str
    user_id: str
    name: str | None = None
    type: str | None = None
    is_default: bool | None = None


class UpdateAccountUseCase:
    def __init__(
        self,
        account_repo: AccountRepositoryPort,
    ) -> None:
        self._account_repo = account_repo

    async def execute(self, inp: UpdateAccountInput) -> UpdateAccountOutput:
        account = await self._account_repo.find_by_id(
            inp.account_id,
        )

        if account is None:
            raise NotFoundError(
                code="ACCOUNT_NOT_FOUND",
                message="Cuenta no encontrada",
            )
        if account.user_id != inp.user_id:
            raise BusinessRuleError(
                code="FORBIDDEN",
                message="No autorizado",
            )
        if account.status == AccountStatus.ARCHIVED:
            raise BusinessRuleError(
                code="ACCOUNT_ARCHIVED",
                message="Cuenta archivada no se puede editar. Restaúrala primero.",
            )
        if inp.name is not None and inp.name != account.name:
            if await self._account_repo.exists_name_for_user(
                inp.user_id,
                inp.name,
            ):
                raise ConflictError(
                    code="ACCOUNT_NAME_TAKEN",
                    message=f"Nombre ya existe: {inp.name}",
                )

            account = account.rename(inp.name)

        if inp.type is not None:
            account = account.change_type(inp.type)
        if inp.is_default is True:
            await self._account_repo.clear_default_for_user(
                inp.user_id,
            )
            account = account.mark_as_default()
        elif inp.is_default is False:
            account = account.unmark_as_default()

        await self._account_repo.save(account)

        return to_account_output(account)
