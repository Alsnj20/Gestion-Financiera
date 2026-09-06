"""JWT Authentication middleware for FastAPI — Reusable auth dependencies."""
from __future__ import annotations

from typing import Protocol

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from modules.auth.infrastructure.jwt_utils import decode_token

security = HTTPBearer()


# ==================== CORE AUTH ====================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Extract and validate JWT token, return user info."""
    token = credentials.credentials
    payload = decode_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN", "message": "Token inválido o expirado"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN_TYPE", "message": "Se requiere token de acceso"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    email = payload.get("email")
    role = payload.get("role", "USER")
    is_verified = payload.get("is_verified", False)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN", "message": "Token inválido"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "user_id": user_id,
        "email": email or "",
        "role": role,
        "is_verified": is_verified,
    }


async def require_admin(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Require admin role."""
    if current_user.get("role") != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "Se requiere rol de administrador"},
        )
    return current_user


async def require_verified(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Require verified account."""
    if not current_user.get("is_verified"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "NOT_VERIFIED", "message": "Cuenta no verificada"},
        )
    return current_user


# ==================== REUSABLE OWNERSHIP CHECK ====================

class OwnedEntity(Protocol):
    """Protocol for entities that have a user_id field."""
    @property
    def user_id(self) -> str: ...


def check_ownership(entity: OwnedEntity, current_user: dict) -> None:
    """
    Validate that the current user owns the entity.
    Raises 403 if not the owner and not admin.
    
    Usage in routers:
        check_ownership(account, current_user)
    """
    if entity.user_id != current_user["user_id"] and current_user["role"] != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "No autorizado"},
        )


def get_user_id_or_admin(target_user_id: str, current_user: dict) -> str:
    """
    For endpoints that take user_id as parameter.
    Returns the user_id if the current user is the owner or admin.
    Raises 403 otherwise.
    
    Usage in routers:
        uid = get_user_id_or_admin(user_id, current_user)
    """
    if target_user_id != current_user["user_id"] and current_user["role"] != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "No autorizado"},
        )
    return current_user["user_id"]
