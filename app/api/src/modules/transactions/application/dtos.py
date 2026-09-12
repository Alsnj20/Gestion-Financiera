"""DTOs de salida unificados del módulo transactions.

Fuente única: `TransactionOutput` + `to_transaction_output`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from modules.transactions.domain.entities.transaction import Transaction


@dataclass(frozen=True, slots=True)
class TransactionOutput:
    id: str
    user_id: str
    account_id: str
    type: str
    amount: Decimal
    currency: str
    description: str
    category_id: str
    payment_method_id: str
    source: str
    status: str
    transaction_date: datetime


def to_transaction_output(tx: Transaction) -> TransactionOutput:
    return TransactionOutput(
        id=tx.id,
        user_id=tx.user_id,
        account_id=tx.account_id,
        type=tx.type.value,
        amount=tx.amount,
        currency=tx.currency,
        description=tx.description,
        category_id=tx.category_id,
        payment_method_id=tx.payment_method_id,
        source=tx.source.value,
        status=tx.status.value,
        transaction_date=tx.transaction_date,
    )


# Aliases de compatibilidad.
CreateTransactionOutput = TransactionOutput
ListTransactionsOutput = TransactionOutput
GetTransactionOutput = TransactionOutput
UpdateTransactionOutput = TransactionOutput
CancelTransactionOutput = TransactionOutput
