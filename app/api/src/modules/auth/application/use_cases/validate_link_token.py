from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from modules.auth.application.ports.whatsapp_link_repository import (
    WhatsAppLinkRepositoryPort,
)
from shared.errors import ValidationError


@dataclass(frozen=True, slots=True)
class ValidateLinkTokenInput:
    token: str


@dataclass(frozen=True, slots=True)
class ValidateLinkTokenOutput:
    valid: bool
    phone_number: str
    already_linked: bool


class ValidateLinkTokenUseCase:
    def __init__(self, link_repo: WhatsAppLinkRepositoryPort) -> None:
        self._link_repo = link_repo

    async def execute(self, inp: ValidateLinkTokenInput) -> ValidateLinkTokenOutput:
        token_data = await self._link_repo.find_by_token(inp.token)

        if not token_data:
            raise ValidationError(
                code="LINK_TOKEN_INVALID",
                message="Token inválido o expirado",
            )

        if token_data["linked"]:
            raise ValidationError(
                code="LINK_TOKEN_USED",
                message="Token ya utilizado",
            )

        if datetime.now(UTC) > token_data["expires_at"]:
            raise ValidationError(
                code="LINK_TOKEN_EXPIRED",
                message="Token inválido o expirado",
            )

        return ValidateLinkTokenOutput(
            valid=True,
            phone_number=token_data["phone_number"],
            already_linked=False,
        )
