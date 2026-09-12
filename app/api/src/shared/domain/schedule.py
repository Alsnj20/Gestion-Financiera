"""Generador de cronograma de cuotas (loans + debts comparten la mecánica).

Reglas:
- Contado = 1 cuota por el total en `first_due_date`.
- Frecuencia SINGLE siempre genera 1 cuota (aunque pidan más).
- Reparto en partes iguales con cuantización a céntimos; el residuo
  de redondeo va en la ÚLTIMA cuota para que la suma sea exacta.
- Interés SIMPLE: PERCENTAGE → principal * tasa/100 como interés total;
  FIXED_AMOUNT → la tasa ya es el interés total.
- FRENCH/GERMAN aún no tienen fórmula propia: usan reparto igual
  (SIMPLE) hasta implementar su matemática.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from shared.types.enums import InterestRateType, PaymentFrequency

_CENT = Decimal("0.01")


@dataclass(frozen=True, slots=True)
class ScheduledInstallment:
    number: int
    due_date: date
    principal_due: Decimal
    interest_due: Decimal
    total_due: Decimal


def add_months(base: date, months: int) -> date:
    """Suma meses calendario respetando fin de mes (31 ene + 1 → 28/29 feb)."""
    month_index = base.month - 1 + months
    year = base.year + month_index // 12
    month = month_index % 12 + 1
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(base.day, last_day))


def step_date(base: date, frequency: PaymentFrequency, steps: int) -> date:
    if frequency == PaymentFrequency.WEEKLY:
        return date.fromordinal(base.toordinal() + 7 * steps)
    if frequency == PaymentFrequency.BIWEEKLY:
        return date.fromordinal(base.toordinal() + 14 * steps)
    return add_months(base, steps)


def split_amount(total: Decimal, parts: int) -> list[Decimal]:
    """Reparte en partes iguales; el residuo va en la última (suma exacta)."""
    if parts <= 1:
        return [total]
    base = (total / parts).quantize(_CENT, rounding=ROUND_HALF_UP)
    last = (total - base * (parts - 1)).quantize(_CENT, rounding=ROUND_HALF_UP)
    return [base] * (parts - 1) + [last]


def total_interest(
    principal: Decimal, rate: Decimal, rate_type: InterestRateType
) -> Decimal:
    if rate_type == InterestRateType.FIXED_AMOUNT:
        return max(rate, Decimal("0.00"))
    return max(
        (principal * rate / Decimal(100)).quantize(_CENT, rounding=ROUND_HALF_UP),
        Decimal("0.00"),
    )


def build_schedule(
    *,
    principal: Decimal,
    interest_rate: Decimal,
    interest_rate_type: InterestRateType,
    installment_count: int,
    frequency: PaymentFrequency,
    first_due_date: date,
) -> list[ScheduledInstallment]:
    """Cronograma puro (sin ids): el módulo lo envuelve en sus entidades."""
    count = (
        1
        if frequency == PaymentFrequency.SINGLE
        else max(int(installment_count or 1), 1)
    )
    interest = total_interest(principal, interest_rate, interest_rate_type)
    principals = split_amount(principal, count)
    interests = split_amount(interest, count)

    return [
        ScheduledInstallment(
            number=n,
            due_date=step_date(first_due_date, frequency, n - 1),
            principal_due=principals[n - 1],
            interest_due=interests[n - 1],
            total_due=principals[n - 1] + interests[n - 1],
        )
        for n in range(1, count + 1)
    ]
