from __future__ import annotations

from datetime import datetime
from typing import Protocol


class RefreshSessionRepositoryPort(Protocol):
    """Persistencia de sesiones refresh (D3: rotación + revocación).

    Solo guarda hashes SHA-256, nunca tokens en claro. La rotación
    posterior no requerirá cambiar use cases ni controller.
    """

    async def create(
        self, user_id: str, token_hash: str, expires_at: datetime
    ) -> None: ...
    async def find_active(self, token_hash: str) -> dict | None: ...
    async def revoke(self, token_hash: str, replaced_by: str | None = None) -> None: ...
    async def revoke_all_for_user(self, user_id: str) -> None: ...
