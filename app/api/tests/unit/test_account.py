"""Unit tests for Account entity."""

from decimal import Decimal

import pytest

from modules.accounts.domain.entities.account import Account
from shared.errors import BusinessRuleError, ValidationError
from shared.types.enums import AccountStatus, AccountType


def test_create_account():
    account = Account.create(
        user_id="user-123",
        name="Mi Cuenta",
        type=AccountType.BANK,
        currency="PEN",
        initial_balance=Decimal("1000.00"),
    )
    assert account.user_id == "user-123"
    assert account.name == "Mi Cuenta"
    assert account.type == AccountType.BANK
    assert account.current_balance == Decimal("1000.00")
    assert account.status == AccountStatus.ACTIVE


def test_apply_income():
    account = Account.create(
        user_id="user-123",
        name="Cuenta",
        initial_balance=Decimal("500.00"),
    )
    updated = account.apply_income(Decimal("200.00"))
    assert updated.current_balance == Decimal("700.00")


def test_apply_expense():
    account = Account.create(
        user_id="user-123",
        name="Cuenta",
        initial_balance=Decimal("500.00"),
    )
    updated = account.apply_expense(Decimal("150.00"))
    assert updated.current_balance == Decimal("350.00")


def test_apply_income_archived_account():
    account = Account.create(
        user_id="user-123",
        name="Cuenta",
        initial_balance=Decimal("500.00"),
    )
    archived = account.archive()
    with pytest.raises(BusinessRuleError) as exc_info:
        archived.apply_income(Decimal("100.00"))
    assert exc_info.value.code == "ACCOUNT_ARCHIVED"


def test_apply_expense_archived_account():
    account = Account.create(
        user_id="user-123",
        name="Cuenta",
        initial_balance=Decimal("500.00"),
    )
    archived = account.archive()
    with pytest.raises(BusinessRuleError) as exc_info:
        archived.apply_expense(Decimal("100.00"))
    assert exc_info.value.code == "ACCOUNT_ARCHIVED"


def test_archive_account():
    account = Account.create(
        user_id="user-123",
        name="Cuenta",
        initial_balance=Decimal("500.00"),
    )
    archived = account.archive()
    assert archived.status == AccountStatus.ARCHIVED


def test_rename_account():
    account = Account.create(
        user_id="user-123",
        name="Cuenta Vieja",
        initial_balance=Decimal("500.00"),
    )
    renamed = account.rename("Cuenta Nueva")
    assert renamed.name == "Cuenta Nueva"


def test_account_name_required():
    with pytest.raises(ValidationError) as exc_info:
        Account.create(user_id="user-123", name="", initial_balance=Decimal("100.00"))
    assert exc_info.value.code == "ACCOUNT_NAME_REQUIRED"


def test_account_user_required():
    with pytest.raises(ValidationError) as exc_info:
        Account.create(user_id="", name="Cuenta", initial_balance=Decimal("100.00"))
    assert exc_info.value.code == "ACCOUNT_USER_REQUIRED"
