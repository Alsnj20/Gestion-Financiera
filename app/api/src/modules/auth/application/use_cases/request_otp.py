from __future__ import annotations

import logging
from dataclasses import dataclass

from modules.auth.application.ports.otp_repository import OtpRepositoryPort
from modules.auth.application.ports.otp_sender import OtpSenderPort
from modules.auth.application.use_cases.send_otp import SendOtpInput, SendOtpUseCase
from modules.users.application.ports.user_repository import UserRepositoryPort

logger = logging.getLogger("auth.otp")


@dataclass(frozen=True, slots=True)
class RequestOtpInput:
    phone: str
    channel: str = "WHATSAPP"


@dataclass(frozen=True, slots=True)
class RequestOtpOutput:
    sent: bool
    code: str | None
    channel: str


class RequestOtpUseCase:
    """Emite el OTP con respuesta genérica anti-enumeración (D6).

    Producción y desarrollo devuelven el mismo contrato: si el número no
    existe, se retorna sent=False sin generar ni enviar nada; el detalle
    USER_FOUND/NOT_FOUND solo va al log de debug, nunca al cliente.
    """

    def __init__(
        self,
        user_repo: UserRepositoryPort,
        otp_repo: OtpRepositoryPort,
        sender: OtpSenderPort,
    ) -> None:
        self._user_repo = user_repo
        self._otp_repo = otp_repo
        self._sender = sender

    async def execute(self, inp: RequestOtpInput) -> RequestOtpOutput:
        user = await self._user_repo.find_by_phone(inp.phone)

        if user is None:
            logger.debug("OTP request USER_NOT_FOUND phone=%s", inp.phone)
            return RequestOtpOutput(sent=False, code=None, channel=inp.channel)

        logger.debug("OTP request USER_FOUND phone=%s", inp.phone)

        result = await SendOtpUseCase(self._otp_repo).execute(
            SendOtpInput(user_id=user.id, channel=inp.channel)
        )
        await self._sender.send(user.phone, inp.channel, result.code)

        return RequestOtpOutput(sent=True, code=result.code, channel=inp.channel)
