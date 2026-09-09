from __future__ import annotations

from dataclasses import dataclass

from modules.users.application.dtos import ListUsersOutput, to_user_output
from modules.users.application.ports.user_repository import UserRepositoryPort
from shared.errors import BusinessRuleError


@dataclass(frozen=True, slots=True)
class ListUsersInput:
    requester_id: str
    requester_role: str = "USER"
    limit: int = 100


class ListUsersUseCase:
    def __init__(self, user_repo: UserRepositoryPort) -> None:
        self._user_repo = user_repo

    async def execute(self, inp: ListUsersInput) -> list[ListUsersOutput]:
        # Directorio de usuarios: solo admin (solo lectura).
        if inp.requester_role != "ADMIN":
            raise BusinessRuleError(
                code="FORBIDDEN",
                message="Se requiere rol de administrador",
            )

        users = await self._user_repo.list_all(limit=inp.limit)
        return [to_user_output(u) for u in users]
