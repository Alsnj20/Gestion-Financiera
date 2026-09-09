"""JWT utilities for authentication."""

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime, timedelta

import jwt

from shared.settings import settings

SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS


def create_access_token(
    user_id: str,
    email: str,
    role: str = "USER",
    is_verified: bool = False,
    expires_at: datetime | None = None,
) -> str:
    expire = expires_at or (
        datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "is_verified": is_verified,
        "type": "access",
        "exp": expire,
        "iat": datetime.now(UTC),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(
    user_id: str,
    email: str,
    expires_at: datetime | None = None,
) -> str:
    expire = expires_at or (
        datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )
    payload = {
        "sub": user_id,
        "email": email,
        "type": "refresh",
        # jti único: dos refresh emitidos el mismo segundo nunca colisionan
        # (la rotación depende de hashes distintos).
        "jti": str(uuid.uuid4()),
        "exp": expire,
        "iat": datetime.now(UTC),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict | None:
    """Validación criptográfica (firma + expiración) siempre, en todo entorno."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def hash_token(token: str) -> str:
    """Huella SHA-256 para persistir sesiones sin guardar el token en claro."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
