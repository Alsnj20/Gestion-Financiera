from __future__ import annotations

from typing import Protocol

from modules.categories.domain.entities.category import Category


class CategoryRepositoryPort(Protocol):
    """Sin borrado físico: anular = archivar (status ARCHIVED + shadow).

    La unicidad es por (usuario, nombre, padre): existe con parent_id.
    """

    async def save(self, category: Category) -> None: ...
    async def find_by_id(
        self, category_id: str, *, for_update: bool = False
    ) -> Category | None: ...
    async def find_by_user(self, user_id: str) -> list[Category]: ...
    async def exists_name_for_user(
        self, user_id: str, name: str, parent_id: str = ""
    ) -> bool: ...
