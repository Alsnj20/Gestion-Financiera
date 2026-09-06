from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from modules.auth.infrastructure.otp_utils import generate_otp, get_otp_expiry
from modules.auth.application.ports.otp_repository import OtpRepositoryPort


@dataclass(frozen=True, slots=True)
class SendOtpInput:
    user_id: str
    channel: str = "WHATSAPP"


@dataclass(frozen=True, slots=True)
class SendOtpOutput:
    code: str
    expires_at: datetime


class SendOtpUseCase:
    def __init__(self, otp_repo: OtpRepositoryPort) -> None:
        self._otp_repo = otp_repo

    async def execute(self, inp: SendOtpInput) -> SendOtpOutput:
        # Rate limit: max 3 codes per 10 minutes
        recent_count = await self._otp_repo.count_recent(inp.user_id, inp.channel, minutes=10)
        if recent_count >= 3:
            raise ValueError("Demasiados códigos solicitados. Espera 10 minutos.")

        code = generate_otp()
        expires_at = get_otp_expiry(minutes=5)

        await self._otp_repo.save(
            user_id=inp.user_id,
            code=code,
            channel=inp.channel,
            purpose="VERIFY",
            expires_at=expires_at,
        )

        return SendOtpOutput(code=code, expires_at=expires_at)
