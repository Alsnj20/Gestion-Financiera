from __future__ import annotations

from typing import Protocol


class OtpSenderPort(Protocol):
    """Envío del OTP por el canal correspondiente.

    El use case no sabe si está en dev o prod: composition inyecta
    el provider según configuración (D8).
    """

    async def send(self, phone: str, channel: str, code: str) -> None: ...
