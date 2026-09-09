from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from modules.auth.application.ports.whatsapp_link_repository import (
    WhatsAppLinkRepositoryPort,
)
from modules.auth.infrastructure.link_token_utils import (
    generate_link_token,
    get_link_token_expiry,
)
from shared.settings import settings


@dataclass(frozen=True, slots=True)
class GenerateLinkTokenInput:
    phone_number: str


@dataclass(frozen=True, slots=True)
class GenerateLinkTokenOutput:
    token: str
    wa_link: str
    expires_at: datetime


class GenerateLinkTokenUseCase:
    def __init__(self, link_repo: WhatsAppLinkRepositoryPort) -> None:
        self._link_repo = link_repo

    async def execute(self, inp: GenerateLinkTokenInput) -> GenerateLinkTokenOutput:
        token = generate_link_token()
        expires_at = get_link_token_expiry(hours=settings.LINK_TOKEN_EXPIRATION_HOURS)

        await self._link_repo.save(
            token=token,
            phone_number=inp.phone_number,
            expires_at=expires_at,
        )

        wa_link = (
            f"https://wa.me/{inp.phone_number.lstrip('+')}?text=%2Fvincular%20{token}"
        )

        return GenerateLinkTokenOutput(
            token=token,
            wa_link=wa_link,
            expires_at=expires_at,
        )
