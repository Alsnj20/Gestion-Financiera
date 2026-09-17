from __future__ import annotations

from dataclasses import dataclass

from modules.tags.application.dtos import GetTagOutput, to_tag_output
from modules.tags.application.ports.tag_repository import TagRepositoryPort
from shared.errors import BusinessRuleError, NotFoundError


@dataclass(frozen=True, slots=True)
class GetTagInput:
    tag_id: str
    requester_id: str
    requester_role: str = "USER"


class GetTagUseCase:
    def __init__(self, repo: TagRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, inp: GetTagInput) -> GetTagOutput:
        tag = await self._repo.find_by_id(inp.tag_id)

        if tag is None:
            raise NotFoundError(
                code="TAG_NOT_FOUND",
                message="Tag no encontrado",
            )

        # Lectura: dueño o admin.
        if tag.user_id != inp.requester_id and inp.requester_role != "ADMIN":
            raise BusinessRuleError(
                code="FORBIDDEN",
                message="No autorizado",
            )

        return to_tag_output(tag)
