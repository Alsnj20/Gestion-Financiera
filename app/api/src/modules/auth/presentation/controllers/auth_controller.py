"""Auth Controller — Orquesta use cases, maneja transacciones, traduce errores."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import asdict
from typing import NoReturn, TypeVar

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from modules.auth.application.ports.otp_repository import OtpRepositoryPort
from modules.auth.application.ports.otp_sender import OtpSenderPort
from modules.auth.application.ports.refresh_session_repository import (
    RefreshSessionRepositoryPort,
)
from modules.auth.application.ports.whatsapp_link_repository import (
    WhatsAppLinkRepositoryPort,
)
from modules.auth.application.use_cases.generate_link_token import (
    GenerateLinkTokenInput,
    GenerateLinkTokenUseCase,
)
from modules.auth.application.use_cases.google_auth import (
    GoogleAuthInput,
    GoogleAuthUseCase,
)
from modules.auth.application.use_cases.link_whatsapp import (
    LinkWhatsAppInput,
    LinkWhatsAppUseCase,
)
from modules.auth.application.use_cases.logout import LogoutInput, LogoutUseCase
from modules.auth.application.use_cases.refresh_token import (
    RefreshTokenInput,
    RefreshTokenUseCase,
)
from modules.auth.application.use_cases.request_otp import (
    RequestOtpInput,
    RequestOtpUseCase,
)
from modules.auth.application.use_cases.validate_link_token import (
    ValidateLinkTokenInput,
    ValidateLinkTokenUseCase,
)
from modules.auth.application.use_cases.verify_user import (
    VerifyUserInput,
    VerifyUserUseCase,
)
from modules.users.application.ports.user_repository import UserRepositoryPort
from shared.errors import (
    BusinessRuleError,
    ConflictError,
    DomainError,
    NotFoundError,
    ValidationError,
)

T = TypeVar("T")

# Tabla única de traducción dominio -> HTTP.
_ERROR_HTTP_STATUS: dict[type[DomainError], int] = {
    ValidationError: 400,
    NotFoundError: 404,
    ConflictError: 409,
    BusinessRuleError: 403,
}

# Códigos con status propio (fuera de la tabla general).
_CODE_HTTP_STATUS: dict[str, int] = {
    "RATE_LIMITED": 429,
    "INVALID_GOOGLE_TOKEN": 401,
    "INVALID_REFRESH_TOKEN": 401,
    "OTP_PROVIDER_NOT_CONFIGURED": 503,
}


def _http_status_for(exc: DomainError) -> int:
    if exc.code in _CODE_HTTP_STATUS:
        return _CODE_HTTP_STATUS[exc.code]
    if isinstance(exc, BusinessRuleError) and exc.code != "FORBIDDEN":
        return 409
    return _ERROR_HTTP_STATUS.get(type(exc), 500)


class AuthController:
    """Recibe los ports inyectados (testeable, sin acoplar presentation a infra)."""

    def __init__(
        self,
        otp_repo: OtpRepositoryPort,
        link_repo: WhatsAppLinkRepositoryPort,
        user_repo: UserRepositoryPort,
        session_repo: RefreshSessionRepositoryPort,
        sender: OtpSenderPort,
        session: AsyncSession,
    ) -> None:
        self._otp_repo = otp_repo
        self._link_repo = link_repo
        self._user_repo = user_repo
        self._session_repo = session_repo
        self._sender = sender
        self._session = session

    async def _run_read(self, fn: Callable[[], Awaitable[T]]) -> T:
        try:
            return await fn()
        except DomainError as exc:
            self._raise(_http_status_for(exc), exc.code, exc.message)

    async def _run_write(self, fn: Callable[[], Awaitable[T]]) -> T:
        try:
            result = await fn()
            await self._session.commit()
            return result
        except DomainError as exc:
            await self._session.rollback()
            self._raise(_http_status_for(exc), exc.code, exc.message)

    async def google_auth(self, inp: GoogleAuthInput) -> dict:
        result = await self._run_write(
            lambda: GoogleAuthUseCase(self._user_repo, self._session_repo).execute(inp)
        )
        return asdict(result)

    async def request_otp(self, inp: RequestOtpInput) -> dict:
        result = await self._run_write(
            lambda: RequestOtpUseCase(
                self._user_repo, self._otp_repo, self._sender
            ).execute(inp)
        )
        return asdict(result)

    async def verify_user(self, inp: VerifyUserInput) -> dict:
        result = await self._run_write(
            lambda: VerifyUserUseCase(self._user_repo, self._otp_repo).execute(inp)
        )
        return asdict(result)

    async def generate_link_token(self, inp: GenerateLinkTokenInput) -> dict:
        result = await self._run_write(
            lambda: GenerateLinkTokenUseCase(self._link_repo).execute(inp)
        )
        return asdict(result)

    async def validate_link_token(self, inp: ValidateLinkTokenInput) -> dict:
        result = await self._run_read(
            lambda: ValidateLinkTokenUseCase(self._link_repo).execute(inp)
        )
        return asdict(result)

    async def link_whatsapp(self, inp: LinkWhatsAppInput) -> dict:
        result = await self._run_write(
            lambda: LinkWhatsAppUseCase(self._link_repo, self._user_repo).execute(inp)
        )
        return asdict(result)

    async def refresh(self, inp: RefreshTokenInput) -> dict:
        result = await self._run_write(
            lambda: RefreshTokenUseCase(self._user_repo, self._session_repo).execute(
                inp
            )
        )
        return asdict(result)

    async def logout(self, inp: LogoutInput) -> None:
        await self._run_write(lambda: LogoutUseCase(self._session_repo).execute(inp))

    @staticmethod
    def _raise(
        status_code: int,
        error_code: str,
        message: str,
    ) -> NoReturn:
        raise HTTPException(
            status_code=status_code,
            detail={
                "code": error_code,
                "message": message,
            },
        )
