from __future__ import annotations

from dataclasses import dataclass

from modules.users.application.dtos import GetUserOutput, to_user_output
from modules.users.application.ports.user_repository import UserRepositoryPort
from shared.errors import BusinessRuleError, NotFoundError


@dataclass(frozen=True, slots=True)
class GetUserInput:
    user_id: str
    requester_id: str
    requester_role: str = "USER"


class GetUserUseCase:
    def __init__(self, user_repo: UserRepositoryPort) -> None:
        self._user_repo = user_repo

    async def execute(self, inp: GetUserInput) -> GetUserOutput:
        user = await self._user_repo.find_by_id(inp.user_id)

        if user is None:
            raise NotFoundError(
                code="USER_NOT_FOUND",
                message="Usuario no encontrado",
            )

        # only lecture access
        if user.id != inp.requester_id and inp.requester_role != "ADMIN":
            raise BusinessRuleError(
                code="FORBIDDEN",
                message="No autorizado",
            )

        return to_user_output(user)
