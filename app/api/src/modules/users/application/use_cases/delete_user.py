from __future__ import annotations

from dataclasses import dataclass

from modules.users.application.ports.user_repository import UserRepositoryPort
from shared.errors import BusinessRuleError, NotFoundError


@dataclass(frozen=True, slots=True)
class DeleteUserInput:
    user_id: str
    requester_role: str = "USER"


class DeleteUserUseCase:
    def __init__(self, user_repo: UserRepositoryPort) -> None:
        self._user_repo = user_repo

    async def execute(self, inp: DeleteUserInput) -> None:
        # Borrado total (CASCADE): solo admin, vía solicitud GDPR.
        if inp.requester_role != "ADMIN":
            raise BusinessRuleError(
                code="FORBIDDEN",
                message="Se requiere rol de administrador",
            )

        user = await self._user_repo.find_by_id(inp.user_id)

        if user is None:
            raise NotFoundError(
                code="USER_NOT_FOUND",
                message="Usuario no encontrado",
            )

        await self._user_repo.delete(inp.user_id)
