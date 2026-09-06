from __future__ import annotations

from typing import Protocol
from modules.audit_logs.domain.entities.audit_log import AuditLog


class AuditLogRepositoryPort(Protocol):
    async def save(self, audit_log: AuditLog) -> None: ...
    async def find_by_id(self, audit_log_id: str) -> AuditLog | None: ...
    async def find_by_user(self, user_id: str) -> list[AuditLog]: ...
