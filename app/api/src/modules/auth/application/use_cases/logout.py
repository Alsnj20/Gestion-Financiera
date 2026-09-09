from __future__ import annotations

from dataclasses import dataclass

from modules.auth.application.ports.refresh_session_repository import (
    RefreshSessionRepositoryPort,
)
from modules.auth.infrastructure.jwt_utils import hash_token


@dataclass(frozen=True, slots=True)
class LogoutInput:
    refresh_token: str


class LogoutUseCase:
    """Revoca la sesión refresh (idempotente: token desconocido = 204 igual)."""

    def __init__(self, session_repo: RefreshSessionRepositoryPort) -> None:
        self._session_repo = session_repo

    async def execute(self, inp: LogoutInput) -> None:
        await self._session_repo.revoke(hash_token(inp.refresh_token))
