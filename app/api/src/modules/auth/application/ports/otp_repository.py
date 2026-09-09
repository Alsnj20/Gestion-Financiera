from __future__ import annotations

from datetime import datetime
from typing import Protocol


class OtpRepositoryPort(Protocol):
    async def save(
        self, user_id: str, code: str, channel: str, purpose: str, expires_at: datetime
    ) -> None: ...
    async def find_latest(
        self, user_id: str, channel: str, purpose: str
    ) -> dict | None: ...
    async def mark_used(self, user_id: str, channel: str, purpose: str) -> None: ...
    async def increment_attempts(
        self, user_id: str, channel: str, purpose: str
    ) -> None: ...
    async def count_recent(self, user_id: str, channel: str, minutes: int) -> int: ...
