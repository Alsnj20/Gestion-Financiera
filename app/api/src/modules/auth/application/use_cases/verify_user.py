from __future__ import annotations

from dataclasses import dataclass

from modules.auth.application.ports.otp_repository import OtpRepositoryPort
from modules.auth.application.use_cases.verify_otp import (
    VerifyOtpInput,
    VerifyOtpUseCase,
)
from modules.users.application.dtos import UserOutput, to_user_output
from modules.users.application.ports.user_repository import UserRepositoryPort
from shared.errors import NotFoundError


@dataclass(frozen=True, slots=True)
class VerifyUserInput:
    phone: str
    code: str
    channel: str = "WHATSAPP"


class VerifyUserUseCase:
    """Valida el OTP y marca la cuenta como verificada (coordina ambos repos)."""

    def __init__(
        self, user_repo: UserRepositoryPort, otp_repo: OtpRepositoryPort
    ) -> None:
        self._user_repo = user_repo
        self._otp_repo = otp_repo

    async def execute(self, inp: VerifyUserInput) -> UserOutput:
        user = await self._user_repo.find_by_phone(inp.phone)

        if user is None:
            raise NotFoundError(
                code="USER_NOT_FOUND",
                message="Usuario no encontrado",
            )

        await VerifyOtpUseCase(self._otp_repo).execute(
            VerifyOtpInput(user_id=user.id, code=inp.code, channel=inp.channel)
        )

        verified_user = user.verify()
        await self._user_repo.save(verified_user)

        return to_user_output(verified_user)
