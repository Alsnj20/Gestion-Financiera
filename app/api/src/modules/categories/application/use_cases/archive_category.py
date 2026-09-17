from __future__ import annotations

from dataclasses import dataclass

from modules.categories.application.ports.category_repository import (
    CategoryRepositoryPort,
)
from shared.errors import BusinessRuleError, NotFoundError


@dataclass(frozen=True, slots=True)
class ArchiveCategoryInput:
    category_id: str
    user_id: str


class ArchiveCategoryUseCase:
    def __init__(self, repo: CategoryRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, inp: ArchiveCategoryInput) -> None:
        category = await self._repo.find_by_id(inp.category_id, for_update=True)

        if category is None:
            raise NotFoundError(
                code="CAT_NOT_FOUND",
                message="Categoría no encontrada",
            )

        # Solo el dueño archiva.
        if category.user_id != inp.user_id:
            raise BusinessRuleError(
                code="FORBIDDEN",
                message="No autorizado",
            )

        # Idempotente: ya archivada no hace nada.
        if category.is_archived():
            return

        # archive_with_shadow_name libera el nombre original.
        await self._repo.save(category.archive_with_shadow_name())
