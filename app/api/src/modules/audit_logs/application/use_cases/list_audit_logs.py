from __future__ import annotations

from dataclasses import dataclass
from modules.audit_logs.domain.entities.audit_log import AuditLog
from modules.audit_logs.application.ports.audit_log_repository import AuditLogRepositoryPort


@dataclass(frozen=True, slots=True)
class ListAuditLogsInput:
    user_id: str


@dataclass(frozen=True, slots=True)
class ListAuditLogsOutput:
    id: str
    user_id: str
    entity_type: str
    entity_id: str
    action: str
    source: str


class ListAuditLogsUseCase:
    def __init__(self, repo: AuditLogRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, inp: ListAuditLogsInput) -> list[ListAuditLogsOutput]:
        items = await self._repo.find_by_user(inp.user_id)
        return [
            ListAuditLogsOutput(
                id=l.id,
                user_id=l.user_id,
                entity_type=l.entity_type,
                entity_id=l.entity_id,
                action=l.action,
                source=l.source,
            )
            for l in items
        ]
