from __future__ import annotations

from dataclasses import dataclass
from modules.categories.domain.entities.category import Category
from modules.categories.application.ports.category_repository import CategoryRepositoryPort
from shared.errors import ConflictError


@dataclass(frozen=True, slots=True)
class CreateCategoryInput:
    user_id: str
    name: str
    type: str = "BOTH"
    parent_id: str = ""


@dataclass(frozen=True, slots=True)
class CreateCategoryOutput:
    id: str
    user_id: str
    name: str
    type: str
    parent_id: str
    status: str


class CreateCategoryUseCase:
    def __init__(self, repo: CategoryRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, inp: CreateCategoryInput) -> CreateCategoryOutput:
        if await self._repo.exists_name_for_user(inp.user_id, inp.name):
            raise ConflictError(code="CAT_NAME_TAKEN", message=f"Categoría ya existe: {inp.name}")

        category = Category.create(user_id=inp.user_id, name=inp.name, type=inp.type, parent_id=inp.parent_id)
        await self._repo.save(category)

        return CreateCategoryOutput(
            id=category.id, user_id=category.user_id, name=category.name,
            type=category.type.value if hasattr(category.type, "value") else str(category.type),
            parent_id=category.parent_id,
            status=category.status.value if hasattr(category.status, "value") else str(category.status),
        )
