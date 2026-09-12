from __future__ import annotations

from dataclasses import dataclass

from modules.auth.application.ports.refresh_session_repository import (
    RefreshSessionRepositoryPort,
)
from modules.auth.infrastructure.google_oauth import verify_google_token
from modules.auth.infrastructure.jwt_utils import (
    create_access_token,
    create_refresh_token,
    hash_token,
)
from modules.users.application.ports.user_repository import UserRepositoryPort
from modules.users.domain.entities.user import User
from shared.errors import BusinessRuleError, ConflictError, ValidationError
from shared.settings import settings


@dataclass(frozen=True, slots=True)
class GoogleAuthInput:
    id_token: str
    phone: str = ""
    timezone: str = "America/Lima"
    currency: str = "PEN"


@dataclass(frozen=True, slots=True)
class GoogleAuthOutput:
    access_token: str
    refresh_token: str
    user_id: str
    email: str
    role: str
    is_verified: bool
    is_new_user: bool


class GoogleAuthUseCase:
    """Login o registro con Google (upsert por email verificado)"""

    def __init__(
        self,
        user_repo: UserRepositoryPort,
        session_repo: RefreshSessionRepositoryPort,
    ) -> None:
        self._user_repo = user_repo
        self._session_repo = session_repo

    async def execute(self, inp: GoogleAuthInput) -> GoogleAuthOutput:
        google_user = verify_google_token(inp.id_token)

        if not google_user:
            raise BusinessRuleError(
                code="INVALID_GOOGLE_TOKEN",
                message="Token de Google inválido o expirado",
            )

        existing_user = await self._user_repo.find_by_email(google_user.email)

        if existing_user:
            user = existing_user
            is_new_user = False
        else:
            if not inp.phone:
                raise ValidationError(
                    code="PHONE_REQUIRED",
                    message="Teléfono requerido para nuevo registro",
                )

            if await self._user_repo.find_by_phone(inp.phone):
                raise ConflictError(
                    code="USER_PHONE_TAKEN",
                    message=f"Teléfono ya registrado: {inp.phone}",
                )

            user = User.create(
                name=google_user.name,
                phone=inp.phone,
                email=google_user.email,
                google_id=google_user.google_id,
                is_verified=True,  # Google ya verificó el email
                timezone=inp.timezone,
                currency=inp.currency,
            )
            # Si otro registro concurrente ganó la carrera, el repo lanza
            # ConflictError (constraint único) en vez de 500.
            await self._user_repo.save(user)
            is_new_user = True

        from datetime import UTC, datetime, timedelta

        refresh_expires_at = datetime.now(UTC) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        refresh_token = create_refresh_token(
            user.id, user.email, expires_at=refresh_expires_at
        )
        await self._session_repo.create(
            user_id=user.id,
            token_hash=hash_token(refresh_token),
            expires_at=refresh_expires_at,
        )

        return GoogleAuthOutput(
            access_token=create_access_token(
                user.id, user.email, user.role, user.is_verified
            ),
            refresh_token=refresh_token,
            user_id=user.id,
            email=user.email,
            role=user.role,
            is_verified=user.is_verified,
            is_new_user=is_new_user,
        )
