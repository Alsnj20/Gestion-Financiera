"""Unit tests for Transfer entity."""

from decimal import Decimal

import pytest

from modules.transfers.domain.entities.transfer import Transfer
from shared.errors import BusinessRuleError, ValidationError


def test_create_transfer():
    transfer = Transfer.create(
        user_id="user-123",
        source_account_id="account-src",
        destination_account_id="account-dst",
        source_transaction_id="tx-src",
        destination_transaction_id="tx-dst",
        amount=Decimal("100.00"),
        currency="PEN",
    )
    assert transfer.user_id == "user-123"
    assert transfer.source_account_id == "account-src"
    assert transfer.destination_account_id == "account-dst"
    assert transfer.amount == Decimal("100.00")


def test_same_account_not_allowed():
    with pytest.raises(BusinessRuleError) as exc_info:
        Transfer.create(
            user_id="user-123",
            source_account_id="account-same",
            destination_account_id="account-same",
            source_transaction_id="tx-src",
            destination_transaction_id="tx-dst",
            amount=Decimal("100.00"),
        )
    assert exc_info.value.code == "TR_SAME_ACCOUNT"


def test_amount_must_be_positive():
    with pytest.raises(ValidationError) as exc_info:
        Transfer.create(
            user_id="user-123",
            source_account_id="account-src",
            destination_account_id="account-dst",
            source_transaction_id="tx-src",
            destination_transaction_id="tx-dst",
            amount=Decimal("-100.00"),
        )
    assert exc_info.value.code == "TR_AMOUNT_NOT_POSITIVE"


def test_user_required():
    with pytest.raises(ValidationError) as exc_info:
        Transfer.create(
            user_id="",
            source_account_id="account-src",
            destination_account_id="account-dst",
            source_transaction_id="tx-src",
            destination_transaction_id="tx-dst",
            amount=Decimal("100.00"),
        )
    assert exc_info.value.code == "TR_USER_REQUIRED"


def test_accounts_required():
    with pytest.raises(ValidationError) as exc_info:
        Transfer.create(
            user_id="user-123",
            source_account_id="",
            destination_account_id="account-dst",
            source_transaction_id="tx-src",
            destination_transaction_id="tx-dst",
            amount=Decimal("100.00"),
        )
    assert exc_info.value.code == "TR_ACCOUNT_REQUIRED"


def test_default_status_active_and_mark_reversed():
    from modules.transfers.domain.entities.transfer import TransferStatus

    transfer = Transfer.create(
        user_id="user-123",
        source_account_id="account-src",
        destination_account_id="account-dst",
        source_transaction_id="tx-src",
        destination_transaction_id="tx-dst",
        amount=Decimal("100.00"),
    )
    assert transfer.status == TransferStatus.ACTIVE
    assert transfer.is_reversed() is False
    reversed_transfer = transfer.mark_reversed()
    assert reversed_transfer.status == TransferStatus.REVERSED
    assert reversed_transfer.is_reversed() is True
    assert reversed_transfer.mark_reversed().status == TransferStatus.REVERSED
