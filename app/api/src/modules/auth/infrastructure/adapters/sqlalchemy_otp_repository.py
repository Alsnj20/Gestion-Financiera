from __future__ import annotations

import uuid
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.models import VerificationCodeModel


class SqlAlchemyOtpRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, user_id: str, code: str, channel: str, purpose: str, expires_at: datetime) -> None:
        model = VerificationCodeModel(
            id=uuid.uuid4(),
            user_id=uuid.UUID(user_id) if _is_uuid(user_id) else uuid.uuid4(),
            code=code,
            channel=channel,
            purpose=purpose,
            expires_at=expires_at,
        )
        self._session.add(model)
        await self._session.flush()

    async def find_latest(self, user_id: str, channel: str, purpose: str) -> dict | None:
        stmt = (
            select(VerificationCodeModel)
            .where(
                VerificationCodeModel.user_id == uuid.UUID(user_id),
                VerificationCodeModel.channel == channel,
                VerificationCodeModel.purpose == purpose,
            )
            .order_by(VerificationCodeModel.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        model = result.scalars().first()
        if not model:
            return None
        return {
            "id": str(model.id),
            "code": model.code,
            "expires_at": model.expires_at,
            "used": model.used,
            "attempts": int(model.attempts),
        }

    async def mark_used(self, user_id: str, channel: str, purpose: str) -> None:
        stmt = (
            select(VerificationCodeModel)
            .where(
                VerificationCodeModel.user_id == uuid.UUID(user_id),
                VerificationCodeModel.channel == channel,
                VerificationCodeModel.purpose == purpose,
            )
            .order_by(VerificationCodeModel.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        model = result.scalars().first()
        if model:
            model.used = True
            await self._session.flush()

    async def increment_attempts(self, user_id: str, channel: str, purpose: str) -> None:
        stmt = (
            select(VerificationCodeModel)
            .where(
                VerificationCodeModel.user_id == uuid.UUID(user_id),
                VerificationCodeModel.channel == channel,
                VerificationCodeModel.purpose == purpose,
            )
            .order_by(VerificationCodeModel.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        model = result.scalars().first()
        if model:
            model.attempts = int(model.attempts) + 1
            await self._session.flush()

    async def count_recent(self, user_id: str, channel: str, minutes: int) -> int:
        from datetime import timedelta, timezone
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        stmt = select(VerificationCodeModel).where(
            VerificationCodeModel.user_id == uuid.UUID(user_id),
            VerificationCodeModel.channel == channel,
            VerificationCodeModel.created_at >= cutoff,
        )
        result = await self._session.execute(stmt)
        return len(result.scalars().all())


def _is_uuid(value: str) -> bool:
    try:
        uuid.UUID(str(value))
        return True
    except Exception:
        return False
