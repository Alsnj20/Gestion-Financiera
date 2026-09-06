from __future__ import annotations

from typing import Protocol
from modules.limits.domain.entities.limit import Limit


class LimitRepositoryPort(Protocol):
    async def save(self, limit: Limit) -> None: ...
    async def find_by_id(self, limit_id: str) -> Limit | None: ...
    async def find_by_user(self, user_id: str) -> list[Limit]: ...
