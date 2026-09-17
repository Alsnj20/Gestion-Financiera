from __future__ import annotations

from typing import Protocol

from modules.limits.domain.entities.limit import Limit


class LimitRepositoryPort(Protocol):
    """Sin borrado físico: anular = archivar (status ARCHIVED)."""

    async def save(self, limit: Limit) -> None: ...
    async def find_by_id(
        self, limit_id: str, *, for_update: bool = False
    ) -> Limit | None: ...
    async def find_by_user(self, user_id: str) -> list[Limit]: ...
