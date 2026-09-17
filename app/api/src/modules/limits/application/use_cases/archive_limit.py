from __future__ import annotations

from dataclasses import dataclass

from modules.limits.application.ports.limit_repository import LimitRepositoryPort
from shared.errors import BusinessRuleError, NotFoundError


@dataclass(frozen=True, slots=True)
class ArchiveLimitInput:
    limit_id: str
    user_id: str


class ArchiveLimitUseCase:
    def __init__(self, repo: LimitRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, inp: ArchiveLimitInput) -> None:
        limit = await self._repo.find_by_id(inp.limit_id, for_update=True)

        if limit is None:
            raise NotFoundError(
                code="LIMIT_NOT_FOUND",
                message="Límite no encontrado",
            )

        # Solo el dueño archiva.
        if limit.user_id != inp.user_id:
            raise BusinessRuleError(
                code="FORBIDDEN",
                message="No autorizado",
            )

        # Idempotente: ya archivado no hace nada.
        if limit.is_archived():
            return

        await self._repo.save(limit.archive())
