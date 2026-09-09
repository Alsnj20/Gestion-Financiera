"""Providers de envío OTP (D8).

- DevelopmentOtpSender: registra el OTP en DEBUG de forma explícita y
  controlada para probar el flujo sin WhatsApp/SMTP. Nunca print().
- NullOtpSender: producción sin proveedor real configurado. Falla en voz
  alta (503) en vez de fingir un envío que nunca ocurrió.
"""

from __future__ import annotations

import logging

from modules.auth.application.ports.otp_sender import OtpSenderPort
from shared.errors import BusinessRuleError

logger = logging.getLogger("auth.otp")


class DevelopmentOtpSender(OtpSenderPort):
    async def send(self, phone: str, channel: str, code: str) -> None:
        logger.debug("DEV OTP phone=%s channel=%s code=%s", phone, channel, code)


class NullOtpSender(OtpSenderPort):
    async def send(self, phone: str, channel: str, code: str) -> None:
        raise BusinessRuleError(
            code="OTP_PROVIDER_NOT_CONFIGURED",
            message="Envío de OTP no configurado",
        )
