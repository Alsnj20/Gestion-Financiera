from __future__ import annotations

from dataclasses import dataclass

from modules.auth.application.ports.otp_repository import OtpRepositoryPort
from modules.auth.infrastructure.otp_utils import is_otp_expired


@dataclass(frozen=True, slots=True)
class VerifyOtpInput:
    user_id: str
    code: str
    channel: str = "WHATSAPP"


class VerifyOtpUseCase:
    def __init__(self, otp_repo: OtpRepositoryPort) -> None:
        self._otp_repo = otp_repo

    async def execute(self, inp: VerifyOtpInput) -> bool:
        latest = await self._otp_repo.find_latest(inp.user_id, inp.channel, "VERIFY")

        if not latest:
            raise ValueError("No se encontró un código de verificación")

        if latest["used"]:
            raise ValueError("El código ya fue utilizado")

        if is_otp_expired(latest["expires_at"]):
            raise ValueError("El código ha expirado. Solicita uno nuevo")

        if latest["attempts"] >= 5:
            raise ValueError("Demasiados intentos. Solicita un nuevo código")

        if latest["code"] != inp.code:
            await self._otp_repo.increment_attempts(inp.user_id, inp.channel, "VERIFY")
            raise ValueError("Código incorrecto")

        await self._otp_repo.mark_used(inp.user_id, inp.channel, "VERIFY")
        return True
