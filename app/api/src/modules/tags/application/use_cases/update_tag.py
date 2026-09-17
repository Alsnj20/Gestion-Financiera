from __future__ import annotations

from dataclasses import dataclass

from modules.tags.application.dtos import UpdateTagOutput, to_tag_output
from modules.tags.application.ports.tag_repository import TagRepositoryPort
from modules.tags.domain.entities.tag import normalize_tag_name
from shared.errors import BusinessRuleError, ConflictError, NotFoundError


@dataclass(frozen=True, slots=True)
class UpdateTagInput:
    tag_id: str
    user_id: str
    name: str | None = None


class UpdateTagUseCase:
    def __init__(self, repo: TagRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, inp: UpdateTagInput) -> UpdateTagOutput:
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

        if inp.name is not None and normalize_tag_name(inp.name) != tag.name:
            if await self._repo.exists_name_for_user(inp.user_id, inp.name):
                raise ConflictError(
                    code="TAG_NAME_TAKEN",
                    message=f"Nombre ya existe: {inp.name}",
                )
            # rename() normaliza (lower/#): preserva el invariante.
            tag = tag.rename(inp.name)

        await self._repo.save(tag)

        return to_tag_output(tag)
