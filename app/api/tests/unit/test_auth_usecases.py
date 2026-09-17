"""Unit tests for Auth use cases + controller (fakes, no DB)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

import modules.auth.application.use_cases.google_auth as google_auth_uc
from modules.auth.application.use_cases.google_auth import (
    GoogleAuthInput,
    GoogleAuthUseCase,
)
from modules.auth.application.use_cases.link_whatsapp import (
    LinkWhatsAppInput,
    LinkWhatsAppUseCase,
)
from modules.auth.application.use_cases.request_otp import (
    RequestOtpInput,
    RequestOtpUseCase,
)
from modules.auth.application.use_cases.verify_user import (
    VerifyUserInput,
    VerifyUserUseCase,
)
from modules.auth.presentation.controllers.auth_controller import AuthController
from modules.users.domain.entities.user import User
from shared.errors import (
    BusinessRuleError,
    ConflictError,
    NotFoundError,
    ValidationError,
)


class FakeUserRepo:
    def __init__(self, users: list[User] | None = None) -> None:
        self.store: dict[str, User] = {u.id: u for u in (users or [])}

    async def save(self, user: User) -> None:
        for u in self.store.values():
            if u.id != user.id and u.phone == user.phone:
                raise ConflictError(code="USER_PHONE_TAKEN", message="dup")
        self.store[user.id] = user

    async def find_by_id(self, user_id: str) -> User | None:
        return self.store.get(user_id)

    async def find_by_phone(self, phone: str) -> User | None:
        return next((u for u in self.store.values() if u.phone == phone.strip()), None)

    async def find_by_email(self, email: str) -> User | None:
        cleaned = email.strip().lower()
        return next((u for u in self.store.values() if u.email == cleaned), None)

    async def exists_by_phone(self, phone: str) -> bool:
        return await self.find_by_phone(phone) is not None

    async def list_all(self, limit: int = 100) -> list[User]:
        return list(self.store.values())[:limit]

    async def delete(self, user_id: str) -> None:
        self.store.pop(user_id, None)


class FakeOtpRepo:
    def __init__(self) -> None:
        self.codes: list[dict] = []

    async def find_latest(
        self, user_id: str, channel: str, purpose: str
    ) -> dict | None:
        return self.codes[-1] if self.codes else None

    async def save(self, **kwargs) -> None:
        self.codes.append(
            {
                "code": kwargs["code"],
                "used": False,
                "attempts": 0,
                "expires_at": kwargs["expires_at"],
            }
        )

    async def mark_used(self, *args) -> None:
        if self.codes:
            self.codes[-1]["used"] = True

    async def increment_attempts(self, *args) -> None:
        if self.codes:
            self.codes[-1]["attempts"] += 1

    async def count_recent(self, user_id: str, channel: str, minutes: int) -> int:
        return len(self.codes)


class FakeLinkRepo:
    def __init__(self, token_data: dict | None = None) -> None:
        self.token_data = token_data

    async def find_by_token(self, token: str) -> dict | None:
        return self.token_data

    async def save(self, **kwargs) -> None:
        pass

    async def link(self, token: str, user_id: str) -> None:
        if self.token_data:
            self.token_data["linked"] = True


class FakeSessionRepo:
    """Fake del RefreshSessionRepositoryPort (hash -> fila)."""

    def __init__(self) -> None:
        self.store: dict[str, dict] = {}

    async def create(self, user_id: str, token_hash: str, expires_at: datetime) -> None:
        self.store[token_hash] = {
            "user_id": user_id,
            "token_hash": token_hash,
            "expires_at": expires_at,
        }

    async def find_active(self, token_hash: str) -> dict | None:
        return self.store.get(token_hash)

    async def revoke(self, token_hash: str, replaced_by: str | None = None) -> None:
        self.store.pop(token_hash, None)

    async def revoke_all_for_user(self, user_id: str) -> None:
        for h in [h for h, s in self.store.items() if s["user_id"] == user_id]:
            del self.store[h]


class FakeOtpSender:
    def __init__(self) -> None:
        self.sent: list[tuple[str, str, str]] = []

    async def send(self, phone: str, channel: str, code: str) -> None:
        self.sent.append((phone, channel, code))


def _controller(
    repo=None, otp_repo=None, link_repo=None, session_repo=None, sender=None
):
    return AuthController(
        otp_repo or FakeOtpRepo(),
        link_repo or FakeLinkRepo(),
        repo or FakeUserRepo(),
        session_repo or FakeSessionRepo(),
        sender or FakeOtpSender(),
        FakeSession(),
    )


class FakeSession:
    async def commit(self) -> None:
        pass

    async def rollback(self) -> None:
        pass


def _google_user(email="g@test.com"):
    return SimpleNamespace(email=email, name="G User", google_id="google-1")


def _user(**kwargs):
    base = {"name": "Juan", "phone": "+51999888777", "email": "juan@test.com"}
    base.update(kwargs)
    return User.create(**base)


# ---------- google upsert ----------


async def test_google_login_existing(monkeypatch):
    monkeypatch.setattr(
        google_auth_uc,
        "verify_google_token",
        lambda token: _google_user("juan@test.com"),
    )
    repo = FakeUserRepo([_user()])
    sessions = FakeSessionRepo()
    out = await GoogleAuthUseCase(repo, sessions).execute(
        GoogleAuthInput(id_token="tok")
    )
    assert out.is_new_user is False
    assert out.email == "juan@test.com"
    assert out.access_token and out.refresh_token
    assert len(sessions.store) == 1  # sesión creada al login


async def test_google_register_new(monkeypatch):
    monkeypatch.setattr(
        google_auth_uc,
        "verify_google_token",
        lambda token: _google_user("new@test.com"),
    )
    repo = FakeUserRepo()
    out = await GoogleAuthUseCase(repo, FakeSessionRepo()).execute(
        GoogleAuthInput(id_token="tok", phone="+51999888777")
    )
    assert out.is_new_user is True
    assert out.is_verified is True


async def test_google_register_requires_phone(monkeypatch):
    monkeypatch.setattr(
        google_auth_uc,
        "verify_google_token",
        lambda token: _google_user("new@test.com"),
    )
    with pytest.raises(ValidationError) as exc:
        await GoogleAuthUseCase(FakeUserRepo(), FakeSessionRepo()).execute(
            GoogleAuthInput(id_token="tok")
        )
    assert exc.value.code == "PHONE_REQUIRED"


async def test_google_register_phone_taken(monkeypatch):
    monkeypatch.setattr(
        google_auth_uc,
        "verify_google_token",
        lambda token: _google_user("new@test.com"),
    )
    repo = FakeUserRepo([_user(phone="+51999888777")])
    with pytest.raises(ConflictError) as exc:
        await GoogleAuthUseCase(repo, FakeSessionRepo()).execute(
            GoogleAuthInput(id_token="tok", phone="+51999888777")
        )
    assert exc.value.code == "USER_PHONE_TAKEN"


async def test_google_invalid_token(monkeypatch):
    monkeypatch.setattr(google_auth_uc, "verify_google_token", lambda token: None)
    with pytest.raises(BusinessRuleError) as exc:
        await GoogleAuthUseCase(FakeUserRepo(), FakeSessionRepo()).execute(
            GoogleAuthInput(id_token="bad")
        )
    assert exc.value.code == "INVALID_GOOGLE_TOKEN"


# ---------- otp (D6: respuesta genérica, sin 404) ----------


async def test_request_otp_unknown_phone_returns_generic():
    sender = FakeOtpSender()
    out = await RequestOtpUseCase(FakeUserRepo(), FakeOtpRepo(), sender).execute(
        RequestOtpInput(phone="+51000000000")
    )
    assert out.sent is False
    assert out.code is None
    assert sender.sent == []  # nada enviado, nada revelado


async def test_request_otp_known_phone_sends():
    user = _user()
    sender = FakeOtpSender()
    out = await RequestOtpUseCase(FakeUserRepo([user]), FakeOtpRepo(), sender).execute(
        RequestOtpInput(phone=user.phone)
    )
    assert out.sent is True
    assert out.code is not None
    assert sender.sent == [(user.phone, "WHATSAPP", out.code)]


async def test_verify_user_marks_verified():
    user = _user()
    assert user.is_verified is False
    repo = FakeUserRepo([user])
    otp = FakeOtpRepo()
    await otp.save(
        user_id=user.id,
        code="123456",
        channel="WHATSAPP",
        purpose="VERIFY",
        expires_at=datetime.now(UTC) + timedelta(minutes=5),
    )
    out = await VerifyUserUseCase(repo, otp).execute(
        VerifyUserInput(phone=user.phone, code="123456")
    )
    assert out.is_verified is True
    assert repo.store[user.id].is_verified is True


async def test_verify_user_wrong_code_maps_400():
    user = _user()
    repo = FakeUserRepo([user])
    otp = FakeOtpRepo()
    await otp.save(
        user_id=user.id,
        code="123456",
        channel="WHATSAPP",
        purpose="VERIFY",
        expires_at=datetime.now(UTC) + timedelta(minutes=5),
    )
    controller = _controller(repo=repo, otp_repo=otp)
    with pytest.raises(HTTPException) as exc:
        await controller.verify_user(VerifyUserInput(phone=user.phone, code="000000"))
    assert exc.value.status_code == 400
    assert exc.value.detail["code"] == "OTP_MISMATCH"


# ---------- link (D5) ----------


async def test_link_whatsapp_missing_user_404():
    link = FakeLinkRepo(
        {
            "linked": False,
            "phone_number": "+51999888777",
            "expires_at": datetime.now(UTC) + timedelta(hours=1),
        }
    )
    with pytest.raises(NotFoundError) as exc:
        await LinkWhatsAppUseCase(link, FakeUserRepo()).execute(
            LinkWhatsAppInput(token="tok", user_id="ghost")
        )
    assert exc.value.code == "USER_NOT_FOUND"


async def test_link_whatsapp_ok():
    user = _user()
    link = FakeLinkRepo(
        {
            "linked": False,
            "phone_number": user.phone,
            "expires_at": datetime.now(UTC) + timedelta(hours=1),
        }
    )
    assert (
        await LinkWhatsAppUseCase(link, FakeUserRepo([user])).execute(
            LinkWhatsAppInput(token="tok", user_id=user.id)
        )
        is True
    )


# ---------- controller mappings (D4) ----------


async def test_controller_google_conflict_maps_409(monkeypatch):
    monkeypatch.setattr(
        google_auth_uc,
        "verify_google_token",
        lambda token: _google_user("new@test.com"),
    )
    repo = FakeUserRepo([_user(phone="+51999888777")])
    controller = _controller(repo=repo)
    with pytest.raises(HTTPException) as exc:
        await controller.google_auth(
            GoogleAuthInput(id_token="tok", phone="+51999888777")
        )
    assert exc.value.status_code == 409
    assert exc.value.detail["code"] == "USER_PHONE_TAKEN"


# ---------- refresh rotation + logout (D3) ----------


async def test_refresh_rotates_and_rejects_reuse(monkeypatch):
    from modules.auth.application.use_cases.refresh_token import (
        RefreshTokenInput,
        RefreshTokenUseCase,
    )

    monkeypatch.setattr(
        google_auth_uc,
        "verify_google_token",
        lambda token: _google_user("new@test.com"),
    )
    repo = FakeUserRepo()
    sessions = FakeSessionRepo()
    login = await GoogleAuthUseCase(repo, sessions).execute(
        GoogleAuthInput(id_token="tok", phone="+51999888777")
    )
    old_refresh = login.refresh_token

    r1 = await RefreshTokenUseCase(repo, sessions).execute(
        RefreshTokenInput(refresh_token=old_refresh)
    )
    assert r1.access_token
    assert r1.refresh_token != old_refresh  # rotado: par nuevo

    with pytest.raises(BusinessRuleError) as exc:
        await RefreshTokenUseCase(repo, sessions).execute(
            RefreshTokenInput(refresh_token=old_refresh)
        )
    assert exc.value.code == "INVALID_REFRESH_TOKEN"  # reutilizado → rechazado


async def test_logout_revokes(monkeypatch):
    from modules.auth.application.use_cases.logout import LogoutInput, LogoutUseCase
    from modules.auth.application.use_cases.refresh_token import (
        RefreshTokenInput,
        RefreshTokenUseCase,
    )

    monkeypatch.setattr(
        google_auth_uc,
        "verify_google_token",
        lambda token: _google_user("new@test.com"),
    )
    repo = FakeUserRepo()
    sessions = FakeSessionRepo()
    login = await GoogleAuthUseCase(repo, sessions).execute(
        GoogleAuthInput(id_token="tok", phone="+51999888777")
    )
    await LogoutUseCase(sessions).execute(
        LogoutInput(refresh_token=login.refresh_token)
    )

    with pytest.raises(BusinessRuleError) as exc:
        await RefreshTokenUseCase(repo, sessions).execute(
            RefreshTokenInput(refresh_token=login.refresh_token)
        )
    assert exc.value.code == "INVALID_REFRESH_TOKEN"
