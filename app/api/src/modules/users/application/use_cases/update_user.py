from __future__ import annotations

from dataclasses import dataclass

from modules.users.application.dtos import UpdateUserOutput, to_user_output
from modules.users.application.ports.user_repository import UserRepositoryPort
from shared.errors import BusinessRuleError, NotFoundError


@dataclass(frozen=True, slots=True)
class UpdateUserInput:
    user_id: str
    requester_id: str
    requester_role: str = "USER"
    name: str | None = None
    email: str | None = None
    timezone: str | None = None
    currency: str | None = None


class UpdateUserUseCase:
    def __init__(self, user_repo: UserRepositoryPort) -> None:
        self._user_repo = user_repo

    async def execute(self, inp: UpdateUserInput) -> UpdateUserOutput:
        user = await self._user_repo.find_by_id(inp.user_id)

        if user is None:
            raise NotFoundError(
                code="USER_NOT_FOUND",
                message="Usuario no encontrado",
            )

        # Escritura: dueño o admin.
        if user.id != inp.requester_id and inp.requester_role != "ADMIN":
            raise BusinessRuleError(
                code="FORBIDDEN",
                message="No autorizado",
            )

        updated = user.update_profile(
            name=inp.name,
            email=inp.email,
            timezone=inp.timezone,
            currency=inp.currency,
        )

        await self._user_repo.save(updated)

        return to_user_output(updated)
