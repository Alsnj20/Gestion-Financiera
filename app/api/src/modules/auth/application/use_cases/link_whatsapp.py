from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from modules.auth.application.ports.whatsapp_link_repository import (
    WhatsAppLinkRepositoryPort,
)
from modules.users.application.ports.user_repository import UserRepositoryPort
from shared.errors import NotFoundError, ValidationError


@dataclass(frozen=True, slots=True)
class LinkWhatsAppInput:
    token: str
    user_id: str


class LinkWhatsAppUseCase:
    def __init__(
        self,
        link_repo: WhatsAppLinkRepositoryPort,
        user_repo: UserRepositoryPort,
    ) -> None:
        self._link_repo = link_repo
        self._user_repo = user_repo

    async def execute(self, inp: LinkWhatsAppInput) -> bool:
        # El usuario debe existir: sin esto se vinculan tokens a user_id fantasma.
        user = await self._user_repo.find_by_id(inp.user_id)
        if user is None:
            raise NotFoundError(
                code="USER_NOT_FOUND",
                message="Usuario no encontrado",
            )

        token_data = await self._link_repo.find_by_token(inp.token)

        if not token_data:
            raise ValidationError(
                code="LINK_TOKEN_INVALID",
                message="Token de vinculación no válido",
            )

        if token_data["linked"]:
            raise ValidationError(
                code="LINK_TOKEN_USED",
                message="Este token ya fue utilizado",
            )

        if datetime.now(UTC) > token_data["expires_at"]:
            raise ValidationError(
                code="LINK_TOKEN_EXPIRED",
                message="Token de vinculación expirado. Solicita uno nuevo",
            )

        await self._link_repo.link(token=inp.token, user_id=inp.user_id)
        return True
