from __future__ import annotations

from dataclasses import dataclass

from modules.auth.application.ports.whatsapp_link_repository import WhatsAppLinkRepositoryPort


@dataclass(frozen=True, slots=True)
class LinkWhatsAppInput:
    token: str
    user_id: str


class LinkWhatsAppUseCase:
    def __init__(self, link_repo: WhatsAppLinkRepositoryPort) -> None:
        self._link_repo = link_repo

    async def execute(self, inp: LinkWhatsAppInput) -> bool:
        token_data = await self._link_repo.find_by_token(inp.token)

        if not token_data:
            raise ValueError("Token de vinculación no válido")

        if token_data["linked"]:
            raise ValueError("Este token ya fue utilizado")

        from datetime import datetime, timezone
        if datetime.now(timezone.utc) > token_data["expires_at"]:
            raise ValueError("Token de vinculación expirado. Solicita uno nuevo")

        await self._link_repo.link(token=inp.token, user_id=inp.user_id)
        return True
