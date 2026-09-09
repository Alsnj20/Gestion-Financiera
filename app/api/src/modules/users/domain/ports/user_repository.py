"""Shim de compatibilidad — usar `modules.users.application.ports`."""
from __future__ import annotations

from modules.users.application.ports.user_repository import UserRepositoryPort

__all__ = ["UserRepositoryPort"]
