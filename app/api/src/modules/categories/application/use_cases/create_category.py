from __future__ import annotations

from dataclasses import dataclass

from modules.categories.application.dtos import CreateCategoryOutput, to_category_output
from modules.categories.application.ports.category_repository import (
    CategoryRepositoryPort,
)
from modules.categories.domain.entities.category import Category
from shared.errors import BusinessRuleError, ConflictError, NotFoundError


@dataclass(frozen=True, slots=True)
class CreateCategoryInput:
    user_id: str
    name: str
    type: str = "BOTH"
    parent_id: str = ""
    icon: str = ""
    color: str = ""


async def _resolve_parent(
    repo: CategoryRepositoryPort, user_id: str, parent_id: str
) -> str:
    """Valida que el padre exista, sea del usuario y no archive la jerarquía."""
    if not parent_id:
        return ""
    parent = await repo.find_by_id(parent_id)
    if parent is None:
        raise NotFoundError(
            code="CAT_PARENT_NOT_FOUND",
            message="Categoría padre no encontrada",
        )
    if parent.user_id != user_id:
        raise BusinessRuleError(
            code="FORBIDDEN",
            message="No autorizado",
        )
    if parent.is_archived():
        raise BusinessRuleError(
            code="CAT_PARENT_ARCHIVED",
            message="La categoría padre está archivada.",
        )
    return parent.id


async def _ensure_no_cycle(
    repo: CategoryRepositoryPort, category_id: str, parent_id: str
) -> None:
    """Camina hacia arriba: el nuevo padre no puede ser descendiente propio."""
    seen = {category_id}
    current_id = parent_id
    while current_id:
        if current_id in seen:
            raise BusinessRuleError(
                code="CAT_CYCLE",
                message="La jerarquía no puede ser cíclica.",
            )
        seen.add(current_id)
        parent = await repo.find_by_id(current_id)
        current_id = parent.parent_id if parent else ""


class CreateCategoryUseCase:
    def __init__(self, repo: CategoryRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, inp: CreateCategoryInput) -> CreateCategoryOutput:
        parent_id = await _resolve_parent(self._repo, inp.user_id, inp.parent_id)

        if await self._repo.exists_name_for_user(inp.user_id, inp.name, parent_id):
            raise ConflictError(
                code="CAT_NAME_TAKEN", message=f"Categoría ya existe: {inp.name}"
            )

        category = Category.create(
            user_id=inp.user_id,
            name=inp.name,
            type=inp.type,
            parent_id=parent_id,
            icon=inp.icon,
            color=inp.color,
        )
        await self._repo.save(category)

        return to_category_output(category)
