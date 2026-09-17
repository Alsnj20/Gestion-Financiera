from __future__ import annotations

from dataclasses import dataclass

from modules.tags.application.ports.tag_repository import TagRepositoryPort
from shared.errors import BusinessRuleError, NotFoundError


@dataclass(frozen=True, slots=True)
class DeleteTagInput:
    tag_id: str
    user_id: str


class DeleteTagUseCase:
    """Borrado físico: tags sin historial; asociaciones caen en cascada."""

    def __init__(self, repo: TagRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, inp: DeleteTagInput) -> None:
        tag = await self._repo.find_by_id(inp.tag_id)

        if tag is None:
            raise NotFoundError(
                code="TAG_NOT_FOUND",
                message="Tag no encontrado",
            )

        # Escritura: solo el dueño (admin solo lee el ledger ajeno).
        if tag.user_id != inp.user_id:
            raise BusinessRuleError(
                code="FORBIDDEN",
                message="No autorizado",
            )

        await self._repo.delete(tag.id)
