from __future__ import annotations

import uuid
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.models import WhatsAppLinkTokenModel


class SqlAlchemyWhatsAppLinkRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, token: str, phone_number: str, expires_at: datetime) -> str:
        model = WhatsAppLinkTokenModel(
            id=uuid.uuid4(),
            token=token,
            phone_number=phone_number,
            expires_at=expires_at,
        )
        self._session.add(model)
        await self._session.flush()
        return str(model.id)

    async def find_by_token(self, token: str) -> dict | None:
        stmt = select(WhatsAppLinkTokenModel).where(WhatsAppLinkTokenModel.token == token)
        result = await self._session.execute(stmt)
        model = result.scalars().first()
        if not model:
            return None
        return {
            "id": str(model.id),
            "token": model.token,
            "phone_number": model.phone_number,
            "user_id": str(model.user_id) if model.user_id else None,
            "linked": model.linked,
            "expires_at": model.expires_at,
        }

    async def link(self, token: str, user_id: str) -> None:
        stmt = select(WhatsAppLinkTokenModel).where(WhatsAppLinkTokenModel.token == token)
        result = await self._session.execute(stmt)
        model = result.scalars().first()
        if model:
            model.linked = True
            model.user_id = uuid.UUID(user_id) if _is_uuid(user_id) else None
            model.linked_at = datetime.utcnow()
            await self._session.flush()

    async def find_by_phone(self, phone_number: str) -> dict | None:
        stmt = (
            select(WhatsAppLinkTokenModel)
            .where(WhatsAppLinkTokenModel.phone_number == phone_number)
            .order_by(WhatsAppLinkTokenModel.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        model = result.scalars().first()
        if not model:
            return None
        return {
            "id": str(model.id),
            "token": model.token,
            "phone_number": model.phone_number,
            "linked": model.linked,
        }


def _is_uuid(value: str) -> bool:
    try:
        uuid.UUID(str(value))
        return True
    except Exception:
        return False
