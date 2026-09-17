from __future__ import annotations

from dataclasses import dataclass

from modules.audit_logs.application.dtos import ListAuditLogsOutput, to_audit_log_output
from modules.audit_logs.application.ports.audit_log_repository import (
    AuditLogRepositoryPort,
)
from shared.errors import BusinessRuleError


@dataclass(frozen=True, slots=True)
class ListAuditLogsInput:
    user_id: str
    requester_id: str
    requester_role: str = "USER"


class ListAuditLogsUseCase:
    def __init__(self, repo: AuditLogRepositoryPort) -> None:
        self._repo = repo

    async def execute(self, inp: ListAuditLogsInput) -> list[ListAuditLogsOutput]:
        # Lectura: dueño o admin.
        if inp.user_id != inp.requester_id and inp.requester_role != "ADMIN":
            raise BusinessRuleError(
                code="FORBIDDEN",
                message="No autorizado",
            )

        items = await self._repo.find_by_user(inp.user_id)
        return [to_audit_log_output(log) for log in items]
