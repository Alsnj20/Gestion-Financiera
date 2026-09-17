from __future__ import annotations

from dataclasses import dataclass

from modules.categories.application.dtos import ListCategoriesOutput, to_category_output
from modules.categories.application.ports.category_repository import (
    CategoryRepositoryPort,
)
from shared.errors import BusinessRuleError
from shared.types.enums import CategoryStatus


@dataclass(frozen=True, slots=True)
class ListCategoriesInput:
    user_id: str
    requester_id: str
    requester_role: str = "USER"
    include_archived: bool = False


class ListCategoriesUseCase:
    def __init__(self, repo: CategoryRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, inp: ListCategoriesInput) -> list[ListCategoriesOutput]:
        # Lectura: dueño o admin.
        if inp.user_id != inp.requester_id and inp.requester_role != "ADMIN":
            raise BusinessRuleError(
                code="FORBIDDEN",
                message="No autorizado",
            )

        categories = await self._repo.find_by_user(inp.user_id)
        if not inp.include_archived:
            categories = [c for c in categories if c.status == CategoryStatus.ACTIVE]
        return [to_category_output(c) for c in categories]
