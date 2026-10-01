"""DTOs de salida unificados del módulo transfers.

Fuente única: `TransferOutput` + `to_transfer_output`.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from modules.transfers.domain.entities.transfer import Transfer


@dataclass(frozen=True, slots=True)
class TransferOutput:
    id: str
    user_id: str
    source_account_id: str
    destination_account_id: str
    amount: Decimal
    currency: str
    status: str


def to_transfer_output(transfer: Transfer) -> TransferOutput:
    return TransferOutput(
        id=transfer.id,
        user_id=transfer.user_id,
        source_account_id=transfer.source_account_id,
        destination_account_id=transfer.destination_account_id,
        amount=transfer.amount,
        currency=transfer.currency,
        status=transfer.status.value,
    )


# Aliases de compatibilidad.
CreateTransferOutput = TransferOutput
GetTransferOutput = TransferOutput
ListTransfersOutput = TransferOutput
ReverseTransferOutput = TransferOutput
