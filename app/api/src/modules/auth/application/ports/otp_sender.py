from __future__ import annotations

from typing import Protocol


class OtpSenderPort(Protocol):
    """Envío del OTP por el canal correspondiente.
    El use case: en dev o prod: composition inyecta
    """

    async def send(self, phone: str, channel: str, code: str) -> None: ...
