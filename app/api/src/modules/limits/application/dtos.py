"""DTOs de salida unificados del módulo limits.

Fuente única: `LimitOutput` + `to_limit_output`.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from modules.limits.domain.entities.limit import Limit


@dataclass(frozen=True, slots=True)
class LimitOutput:
    id: str
    user_id: str
    name: str
    amount: Decimal
    period_type: str
    category_id: str
    threshold_warning: Decimal
    status: str


def to_limit_output(limit: Limit) -> LimitOutput:
    return LimitOutput(
        id=limit.id,
        user_id=limit.user_id,
        name=limit.name,
        amount=limit.amount,
        period_type=limit.period_type.value,
        category_id=limit.category_id,
        threshold_warning=limit.threshold_warning,
        status=limit.status.value,
    )


# Aliases de compatibilidad.
CreateLimitOutput = LimitOutput
GetLimitOutput = LimitOutput
ListLimitsOutput = LimitOutput
UpdateLimitOutput = LimitOutput
RestoreLimitOutput = LimitOutput
