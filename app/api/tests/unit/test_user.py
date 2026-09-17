"""Unit tests for User entity."""

from datetime import UTC, datetime

import pytest

from modules.users.domain.entities.user import User
from shared.errors import ValidationError


def test_create_user():
    user = User.create(
        name="Juan Pérez",
        phone="+51999888777",
        email="juan@test.com",
    )
    assert user.name == "Juan Pérez"
    assert user.phone == "+51999888777"
    assert user.email == "juan@test.com"
    assert user.id
    assert user.role == "USER"
    assert user.is_verified is False
    assert user.timezone == "America/Lima"
    assert user.currency == "PEN"


def test_create_user_with_google():
    user = User.create(
        name="Google User",
        phone="+51988777666",
        email="user@gmail.com",
        google_id="google-123",
        is_verified=True,
    )
    assert user.email == "user@gmail.com"
    assert user.google_id == "google-123"
    assert user.is_verified is True


def test_user_name_required():
    with pytest.raises(ValidationError) as exc_info:
        User.create(name="", phone="+51999888777")
    assert exc_info.value.code == "USER_NAME_REQUIRED"


def test_user_phone_invalid():
    with pytest.raises(ValidationError) as exc_info:
        User.create(name="Test", phone="123")
    assert exc_info.value.code == "USER_PHONE_INVALID"


def test_user_email_invalid():
    with pytest.raises(ValidationError) as exc_info:
        User.create(name="Test", phone="+51999888777", email="invalid-email")
    assert exc_info.value.code == "USER_EMAIL_INVALID"


def test_update_profile():
    user = User.create(
        name="Juan",
        phone="+51999888777",
        email="juan@test.com",
    )
    updated = user.update_profile(name="Juan Pérez", email="nuevo@test.com")
    assert updated.name == "Juan Pérez"
    assert updated.email == "nuevo@test.com"
    assert updated.phone == "+51999888777"


def test_verify_user():
    user = User.create(
        name="Test",
        phone="+51999888777",
        email="test@test.com",
    )
    assert user.is_verified is False
    verified = user.verify()
    assert verified.is_verified is True


def test_rehydrate_user():
    now = datetime.now(UTC)
    user = User.rehydrate(
        id="test-id-123",
        name="Test User",
        phone="+51999888777",
        email="test@test.com",
        role="ADMIN",
        is_verified=True,
        google_id="google-456",
        created_at=now,
        updated_at=now,
    )
    assert user.id == "test-id-123"
    assert user.role == "ADMIN"
    assert user.is_verified is True
    assert user.google_id == "google-456"
