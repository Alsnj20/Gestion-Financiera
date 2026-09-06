from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from modules.auth.application.ports.whatsapp_link_repository import WhatsAppLinkRepositoryPort


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
            return ValidateLinkTokenOutput(valid=False, phone_number="", already_linked=False)

        if token_data["linked"]:
            return ValidateLinkTokenOutput(
                valid=False,
                phone_number=token_data["phone_number"],
                already_linked=True,
            )

        if datetime.now(timezone.utc) > token_data["expires_at"]:
            return ValidateLinkTokenOutput(valid=False, phone_number="", already_linked=False)

        return ValidateLinkTokenOutput(
            valid=True,
            phone_number=token_data["phone_number"],
            already_linked=False,
        )
