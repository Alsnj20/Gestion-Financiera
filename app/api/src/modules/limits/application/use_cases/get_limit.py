from __future__ import annotations

from dataclasses import dataclass

from modules.limits.application.dtos import GetLimitOutput, to_limit_output
from modules.limits.application.ports.limit_repository import LimitRepositoryPort
from shared.errors import BusinessRuleError, NotFoundError


@dataclass(frozen=True, slots=True)
class GetLimitInput:
    limit_id: str
    requester_id: str
    requester_role: str = "USER"


class GetLimitUseCase:
    def __init__(self, repo: LimitRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, inp: GetLimitInput) -> GetLimitOutput:
        limit = await self._repo.find_by_id(inp.limit_id)

        if limit is None:
            raise NotFoundError(
                code="LIMIT_NOT_FOUND",
                message="Límite no encontrado",
            )

        # Lectura: dueño o admin.
        if limit.user_id != inp.requester_id and inp.requester_role != "ADMIN":
            raise BusinessRuleError(
                code="FORBIDDEN",
                message="No autorizado",
            )

        return to_limit_output(limit)
