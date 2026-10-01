"""Seed de usuario para desarrollo local.

Crea (o reutiliza) un usuario ADMIN de prueba y emite un par de tokens
listos para pegar en el panel "Acceso desarrollo" del login.

Uso:
    cd app/api
    PYTHONPATH=src uv run python scripts/seed_dev_user.py [--phone +51999888777]
"""
from __future__ import annotations

import argparse
import asyncio
import sys
import uuid
from datetime import UTC, datetime, timedelta

sys.path.insert(0, "src")

from infrastructure.database.models import UserModel
from infrastructure.database.session import SessionLocal
from modules.auth.infrastructure.jwt_utils import (
    create_access_token,
    create_refresh_token,
    hash_token,
)
from modules.auth.infrastructure.adapters.sqlalchemy_refresh_session_repository import (
    SqlAlchemyRefreshSessionRepository,
)
from shared.settings import settings


async def main(phone: str) -> None:
    async with SessionLocal() as session:
        from sqlalchemy import select

        existing = (
            await session.execute(select(UserModel).where(UserModel.phone == phone))
        ).scalars().first()

        if existing:
            user_id, email, role, verified = (
                str(existing.id),
                existing.email,
                existing.role,
                existing.is_verified,
            )
            print(f"Usuario existente: {email} ({role})")
        else:
            user_id = str(uuid.uuid4())
            email = "dev@finai.local"
            session.add(
                UserModel(
                    id=uuid.UUID(user_id),
                    name="Dev Admin",
                    phone=phone,
                    email=email,
                    role="ADMIN",
                    is_verified=True,
                    google_id="",
                    timezone="America/Lima",
                    currency="PEN",
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC),
                )
            )
            await session.flush()
            role, verified = "ADMIN", True
            print(f"Usuario creado: {email} (ADMIN)")

        refresh_expires = datetime.now(UTC) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        refresh = create_refresh_token(user_id, email, expires_at=refresh_expires)
        access = create_access_token(user_id, email, role, verified)
        await SqlAlchemyRefreshSessionRepository(session).create(
            user_id=user_id, token_hash=hash_token(refresh), expires_at=refresh_expires
        )
        await session.commit()

    print()
    print("ACCESS_TOKEN (15 min):")
    print(access)
    print()
    print("REFRESH_TOKEN (7 días, con rotación):")
    print(refresh)
    print()
    print("Pégalo en http://localhost:3000/login → 'Acceso desarrollo'.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--phone", default="+51999888777")
    args = parser.parse_args()
    asyncio.run(main(args.phone))
