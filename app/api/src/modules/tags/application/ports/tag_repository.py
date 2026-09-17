from __future__ import annotations

from typing import Protocol

from modules.tags.domain.entities.tag import Tag


class TagRepositoryPort(Protocol):
    """Etiquetas puras sin historial: borrado físico permitido.

    Las asociaciones transaction_tags caen en cascada por FK.
    """

    async def save(self, tag: Tag) -> None: ...
    async def find_by_id(
        self, tag_id: str, *, for_update: bool = False
    ) -> Tag | None: ...
    async def find_by_user(self, user_id: str) -> list[Tag]: ...
    async def exists_name_for_user(self, user_id: str, name: str) -> bool: ...
    async def delete(self, tag_id: str) -> None: ...
