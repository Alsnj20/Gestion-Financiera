from __future__ import annotations

from dataclasses import dataclass

from modules.tags.application.dtos import ListTagsOutput, to_tag_output
from modules.tags.application.ports.tag_repository import TagRepositoryPort
from shared.errors import BusinessRuleError


@dataclass(frozen=True, slots=True)
class ListTagsInput:
    user_id: str
    requester_id: str
    requester_role: str = "USER"


class ListTagsUseCase:
    def __init__(self, repo: TagRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, inp: ListTagsInput) -> list[ListTagsOutput]:
        # Lectura: dueño o admin.
        if inp.user_id != inp.requester_id and inp.requester_role != "ADMIN":
            raise BusinessRuleError(
                code="FORBIDDEN",
                message="No autorizado",
            )

        tags = await self._repo.find_by_user(inp.user_id)
        return [to_tag_output(t) for t in tags]
