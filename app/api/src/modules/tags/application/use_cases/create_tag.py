from __future__ import annotations

from dataclasses import dataclass

from modules.tags.application.dtos import CreateTagOutput, to_tag_output
from modules.tags.application.ports.tag_repository import TagRepositoryPort
from modules.tags.domain.entities.tag import Tag
from shared.errors import ConflictError


@dataclass(frozen=True, slots=True)
class CreateTagInput:
    user_id: str
    name: str


class CreateTagUseCase:
    def __init__(self, repo: TagRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, inp: CreateTagInput) -> CreateTagOutput:
        if await self._repo.exists_name_for_user(inp.user_id, inp.name):
            raise ConflictError(
                code="TAG_NAME_TAKEN", message=f"Tag ya existe: {inp.name}"
            )

        tag = Tag.create(user_id=inp.user_id, name=inp.name)
        await self._repo.save(tag)

        return to_tag_output(tag)
