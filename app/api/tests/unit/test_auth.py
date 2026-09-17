"""Unit tests for JWT utilities."""

from modules.auth.infrastructure.jwt_utils import (
    create_access_token,
    create_refresh_token,
    decode_token,
)


def test_create_access_token():
    token = create_access_token("user-123", "test@test.com")
    assert token
    assert isinstance(token, str)


def test_create_refresh_token():
    token = create_refresh_token("user-123", "test@test.com")
    assert token
    assert isinstance(token, str)


def test_decode_valid_token():
    token = create_access_token("user-123", "test@test.com")
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == "user-123"
    assert payload["email"] == "test@test.com"
    assert payload["type"] == "access"


def test_decode_refresh_token():
    token = create_refresh_token("user-123", "test@test.com")
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == "user-123"
    assert payload["type"] == "refresh"


def test_decode_invalid_token():
    payload = decode_token("invalid.token.here")
    assert payload is None


def test_decode_empty_token():
    payload = decode_token("")
    assert payload is None
