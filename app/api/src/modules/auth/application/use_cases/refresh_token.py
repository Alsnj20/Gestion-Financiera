from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from modules.auth.application.ports.refresh_session_repository import (
    RefreshSessionRepositoryPort,
)
from modules.auth.infrastructure.jwt_utils import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_token,
)
from modules.users.application.ports.user_repository import UserRepositoryPort
from shared.errors import BusinessRuleError
from shared.settings import settings


@dataclass(frozen=True, slots=True)
class RefreshTokenInput:
    refresh_token: str


@dataclass(frozen=True, slots=True)
class RefreshTokenOutput:
    access_token: str
    refresh_token: str


class RefreshTokenUseCase:
    """Renovación con rotación (D3).

    Cada uso válido invalida el refresh anterior y emite un par nuevo.
    Un refresh reutilizado (ya rotado/revocado) o sin sesión se rechaza:
    los tokens legacy sin sesión requieren re-login.
    """

    def __init__(
        self,
        user_repo: UserRepositoryPort,
        session_repo: RefreshSessionRepositoryPort,
    ) -> None:
        self._user_repo = user_repo
        self._session_repo = session_repo

    async def execute(self, inp: RefreshTokenInput) -> RefreshTokenOutput:
        token_data = decode_token(inp.refresh_token)

        if not token_data or token_data.get("type") != "refresh":
            raise BusinessRuleError(
                code="INVALID_REFRESH_TOKEN",
                message="Token de refresco inválido o expirado",
            )

        user_id = token_data.get("sub")
        email = token_data.get("email")

        if not user_id or not email:
            raise BusinessRuleError(
                code="INVALID_REFRESH_TOKEN",
                message="Token de refresco inválido",
            )

        old_hash = hash_token(inp.refresh_token)
        session = await self._session_repo.find_active(old_hash)

        if session is None or datetime.now(UTC) > session["expires_at"]:
            raise BusinessRuleError(
                code="INVALID_REFRESH_TOKEN",
                message="Sesión inválida o expirada. Inicia sesión de nuevo",
            )

        user = await self._user_repo.find_by_id(user_id)

        if not user:
            raise BusinessRuleError(
                code="INVALID_REFRESH_TOKEN",
                message="Usuario no encontrado",
            )

        refresh_expires_at = datetime.now(UTC) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        new_refresh = create_refresh_token(
            user.id, user.email, expires_at=refresh_expires_at
        )
        new_hash = hash_token(new_refresh)

        await self._session_repo.revoke(old_hash, replaced_by=new_hash)
        await self._session_repo.create(
            user_id=user.id, token_hash=new_hash, expires_at=refresh_expires_at
        )

        return RefreshTokenOutput(
            access_token=create_access_token(
                user.id, user.email, user.role, user.is_verified
            ),
            refresh_token=new_refresh,
        )
