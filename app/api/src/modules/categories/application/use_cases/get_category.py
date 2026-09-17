from __future__ import annotations

from dataclasses import dataclass

from modules.categories.application.dtos import GetCategoryOutput, to_category_output
from modules.categories.application.ports.category_repository import (
    CategoryRepositoryPort,
)
from shared.errors import BusinessRuleError, NotFoundError


@dataclass(frozen=True, slots=True)
class GetCategoryInput:
    category_id: str
    requester_id: str
    requester_role: str = "USER"


class GetCategoryUseCase:
    def __init__(self, repo: CategoryRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, inp: GetCategoryInput) -> GetCategoryOutput:
        category = await self._repo.find_by_id(inp.category_id)

        if category is None:
            raise NotFoundError(
                code="CAT_NOT_FOUND",
                message="Categoría no encontrada",
            )

        # Lectura: dueño o admin.
        if category.user_id != inp.requester_id and inp.requester_role != "ADMIN":
            raise BusinessRuleError(
                code="FORBIDDEN",
                message="No autorizado",
            )

        return to_category_output(category)
