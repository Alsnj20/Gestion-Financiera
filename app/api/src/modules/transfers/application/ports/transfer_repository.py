from __future__ import annotations

from typing import Protocol

from modules.transfers.domain.entities.transfer import Transfer


class TransferRepositoryPort(Protocol):
    """Sin borrado físico: la reversión es lógica (status REVERSED)."""

    async def save(self, transfer: Transfer) -> None: ...
    async def find_by_id(
        self, transfer_id: str, *, for_update: bool = False
    ) -> Transfer | None: ...
    async def find_by_user(self, user_id: str) -> list[Transfer]: ...
