"""DTOs de salida unificados del módulo payment_methods.

Fuente única: `PaymentMethodOutput` + `to_payment_method_output`.
"""

from __future__ import annotations

from dataclasses import dataclass

from modules.payment_methods.domain.entities.payment_method import PaymentMethod


@dataclass(frozen=True, slots=True)
class PaymentMethodOutput:
    id: str
    user_id: str
    account_id: str
    name: str
    type: str
    is_default: bool
    status: str


def to_payment_method_output(pm: PaymentMethod) -> PaymentMethodOutput:
    return PaymentMethodOutput(
        id=pm.id,
        user_id=pm.user_id,
        account_id=pm.account_id,
        name=pm.name,
        type=pm.type,
        is_default=pm.is_default,
        status=pm.status.value,
    )


# Aliases de compatibilidad.
CreatePaymentMethodOutput = PaymentMethodOutput
GetPaymentMethodOutput = PaymentMethodOutput
ListPaymentMethodsOutput = PaymentMethodOutput
UpdatePaymentMethodOutput = PaymentMethodOutput
RestorePaymentMethodOutput = PaymentMethodOutput
