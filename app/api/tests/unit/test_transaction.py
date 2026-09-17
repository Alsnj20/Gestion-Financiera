"""Unit tests for Transaction entity."""

from decimal import Decimal

import pytest

from modules.transactions.domain.entities.transaction import Transaction
from shared.errors import ValidationError
from shared.types.enums import TransactionSource, TransactionStatus, TransactionType


def test_create_expense():
    tx = Transaction.create_expense(
        user_id="user-123",
        account_id="account-123",
        amount=Decimal("50.00"),
        currency="PEN",
        description="Compra en tienda",
    )
    assert tx.type == TransactionType.EXPENSE
    assert tx.amount == Decimal("50.00")
    assert tx.status == TransactionStatus.COMPLETED
    assert tx.source == TransactionSource.MANUAL


def test_create_income():
    tx = Transaction.create_income(
        user_id="user-123",
        account_id="account-123",
        amount=Decimal("1000.00"),
        currency="PEN",
        description="Salario",
    )
    assert tx.type == TransactionType.INCOME
    assert tx.amount == Decimal("1000.00")


def test_amount_must_be_positive():
    with pytest.raises(ValidationError) as exc_info:
        Transaction.create_expense(
            user_id="user-123",
            account_id="account-123",
            amount=Decimal("-50.00"),
        )
    assert exc_info.value.code == "TX_AMOUNT_NOT_POSITIVE"


def test_user_required():
    with pytest.raises(ValidationError) as exc_info:
        Transaction.create_expense(
            user_id="",
            account_id="account-123",
            amount=Decimal("50.00"),
        )
    assert exc_info.value.code == "TX_USER_REQUIRED"


def test_account_required():
    with pytest.raises(ValidationError) as exc_info:
        Transaction.create_expense(
            user_id="user-123",
            account_id="",
            amount=Decimal("50.00"),
        )
    assert exc_info.value.code == "TX_ACCOUNT_REQUIRED"


def test_cancel_transaction():
    tx = Transaction.create_expense(
        user_id="user-123",
        account_id="account-123",
        amount=Decimal("50.00"),
    )
    cancelled = tx.cancel()
    assert cancelled.status == TransactionStatus.CANCELLED


def test_description_too_long():
    with pytest.raises(ValidationError) as exc_info:
        Transaction.create_expense(
            user_id="user-123",
            account_id="account-123",
            amount=Decimal("50.00"),
            description="x" * 501,
        )
    assert exc_info.value.code == "TX_DESC_TOO_LONG"


def test_is_expense():
    tx = Transaction.create_expense(
        user_id="user-123",
        account_id="account-123",
        amount=Decimal("50.00"),
    )
    assert tx.is_expense() is True
    assert tx.is_income() is False


def test_is_income():
    tx = Transaction.create_income(
        user_id="user-123",
        account_id="account-123",
        amount=Decimal("50.00"),
    )
    assert tx.is_income() is True
    assert tx.is_expense() is False


def test_pending_status_rejected():
    """PENDING vive en pagos programados, no en el ledger."""
    with pytest.raises(ValidationError) as exc_info:
        Transaction(
            id="tx-1",
            user_id="user-123",
            account_id="account-123",
            type=TransactionType.EXPENSE,
            amount=Decimal("50.00"),
            status="PENDING",
        )
    assert exc_info.value.code == "TX_STATUS_INVALID"
