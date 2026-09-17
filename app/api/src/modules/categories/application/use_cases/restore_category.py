from __future__ import annotations

from dataclasses import dataclass

from modules.categories.application.dtos import (
    RestoreCategoryOutput,
    to_category_output,
)
from modules.categories.application.ports.category_repository import (
    CategoryRepositoryPort,
)
from shared.domain.guards import shadow_original_name
from shared.errors import BusinessRuleError, ConflictError, NotFoundError


@dataclass(frozen=True, slots=True)
class RestoreCategoryInput:
    category_id: str
    user_id: str


class RestoreCategoryUseCase:
    def __init__(self, repo: CategoryRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, inp: RestoreCategoryInput) -> RestoreCategoryOutput:
        category = await self._repo.find_by_id(inp.category_id, for_update=True)

        if category is None:
            raise NotFoundError(
                code="CAT_NOT_FOUND",
                message="Categoría no encontrada",
            )

        # Solo el dueño restaura.
        if category.user_id != inp.user_id:
            raise BusinessRuleError(
                code="FORBIDDEN",
                message="No autorizado",
            )

        if not category.is_archived():
            raise BusinessRuleError(
                code="CAT_NOT_ARCHIVED",
                message="Solo se puede restaurar una categoría archivada.",
            )

        original = shadow_original_name(category.name)
        if await self._repo.exists_name_for_user(
            inp.user_id, original, category.parent_id
        ):
            raise ConflictError(
                code="CAT_NAME_TAKEN",
                message=f"Ya existe una categoría con el nombre: {original}",
            )

        restored = category.restore(original)
        await self._repo.save(restored)

        return to_category_output(restored)
