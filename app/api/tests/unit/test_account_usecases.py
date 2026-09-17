"""Unit tests for Account use cases + controller (fake repo, no DB)."""

from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi import HTTPException

from modules.accounts.application.use_cases.archive_account import (
    ArchiveAccountInput,
    ArchiveAccountUseCase,
)
from modules.accounts.application.use_cases.create_account import (
    CreateAccountInput,
    CreateAccountUseCase,
)
from modules.accounts.application.use_cases.get_account import (
    GetAccountInput,
    GetAccountUseCase,
)
from modules.accounts.application.use_cases.list_accounts import (
    ListAccountsByUserInput,
    ListAccountsByUserUseCase,
)
from modules.accounts.application.use_cases.restore_account import (
    RestoreAccountInput,
    RestoreAccountUseCase,
)
from modules.accounts.application.use_cases.update_account import (
    UpdateAccountInput,
    UpdateAccountUseCase,
)
from modules.accounts.domain.entities.account import Account
from modules.accounts.presentation.controllers.account_controller import (
    AccountController,
)
from shared.errors import BusinessRuleError, ConflictError, NotFoundError
from shared.types.enums import AccountStatus


class FakeAccountRepository:
    """In-memory port implementation."""

    def __init__(self, accounts: list[Account] | None = None) -> None:
        self.store: dict[str, Account] = {a.id: a for a in (accounts or [])}

    async def save(self, account: Account) -> None:
        self.store[account.id] = account

    async def find_by_id(
        self, account_id: str, *, for_update: bool = False
    ) -> Account | None:
        return self.store.get(account_id)

    async def find_by_user(self, user_id: str) -> list[Account]:
        return [a for a in self.store.values() if a.user_id == user_id]

    async def clear_default_for_user(self, user_id: str) -> None:
        for a in list(self.store.values()):
            if a.user_id == user_id and a.is_default:
                self.store[a.id] = a.unmark_as_default()

    async def exists_name_for_user(self, user_id: str, name: str) -> bool:
        return any(
            a
            for a in self.store.values()
            if a.user_id == user_id and a.name == name.strip()
        )


class FakeSession:
    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        self.rollbacks += 1


def _account(**kwargs) -> Account:
    base = {"user_id": "user-1", "name": "Ahorros"}
    base.update(kwargs)
    return Account.create(**base)


# ---------- create ----------


async def test_create_marks_default_clears_others():
    repo = FakeAccountRepository([_account(name="Vieja", is_default=True)])
    out = await CreateAccountUseCase(repo).execute(
        CreateAccountInput(user_id="user-1", name="Nueva", is_default=True)
    )
    assert out.is_default is True
    defaults = [a for a in repo.store.values() if a.is_default]
    assert len(defaults) == 1
    assert defaults[0].id == out.id


async def test_create_duplicate_name_conflict():
    repo = FakeAccountRepository([_account(name="Ahorros")])
    with pytest.raises(ConflictError):
        await CreateAccountUseCase(repo).execute(
            CreateAccountInput(user_id="user-1", name="Ahorros")
        )


# ---------- update ----------


async def test_update_rename_collision_conflict():
    repo = FakeAccountRepository([_account(name="A"), _account(name="B")])
    acc = next(a for a in repo.store.values() if a.name == "A")
    with pytest.raises(ConflictError):
        await UpdateAccountUseCase(repo).execute(
            UpdateAccountInput(account_id=acc.id, user_id="user-1", name="B")
        )


async def test_update_forbidden_for_other_user():
    repo = FakeAccountRepository([_account(name="A")])
    acc = next(iter(repo.store.values()))
    with pytest.raises(BusinessRuleError):
        await UpdateAccountUseCase(repo).execute(
            UpdateAccountInput(account_id=acc.id, user_id="other", name="X")
        )


async def test_update_not_found():
    with pytest.raises(NotFoundError):
        await UpdateAccountUseCase(FakeAccountRepository()).execute(
            UpdateAccountInput(account_id="missing", user_id="user-1", name="X")
        )


# ---------- archive (shadow rename) ----------


async def test_archive_renames_and_unmarks_default():
    repo = FakeAccountRepository(
        [
            _account(name="Ahorros", is_default=True),
            _account(name="Sueldo"),
        ]
    )
    acc = next(a for a in repo.store.values() if a.name == "Ahorros")
    await ArchiveAccountUseCase(repo).execute(
        ArchiveAccountInput(account_id=acc.id, user_id="user-1")
    )
    saved = repo.store[acc.id]
    assert saved.status == AccountStatus.ARCHIVED
    assert saved.is_default is False
    assert saved.name.startswith("Ahorros_deleted_")
    assert saved.name != "Ahorros"


async def test_archive_frees_original_name():
    repo = FakeAccountRepository(
        [
            _account(name="Ahorros"),
            _account(name="Sueldo"),
        ]
    )
    acc = next(a for a in repo.store.values() if a.name == "Ahorros")
    await ArchiveAccountUseCase(repo).execute(
        ArchiveAccountInput(account_id=acc.id, user_id="user-1")
    )
    # El nombre original queda libre para recrear (caso WhatsApp).
    assert not await repo.exists_name_for_user("user-1", "Ahorros")


async def test_archive_is_idempotent():
    repo = FakeAccountRepository(
        [
            _account(name="Ahorros"),
            _account(name="Sueldo"),
        ]
    )
    acc = next(a for a in repo.store.values() if a.name == "Ahorros")
    uc = ArchiveAccountUseCase(repo)
    await uc.execute(ArchiveAccountInput(account_id=acc.id, user_id="user-1"))
    first = repo.store[acc.id].name
    await uc.execute(ArchiveAccountInput(account_id=acc.id, user_id="user-1"))
    assert repo.store[acc.id].name == first  # sin doble sufijo


async def test_archive_last_active_blocked():
    repo = FakeAccountRepository([_account(name="Única")])
    acc = next(iter(repo.store.values()))
    with pytest.raises(BusinessRuleError) as exc:
        await ArchiveAccountUseCase(repo).execute(
            ArchiveAccountInput(account_id=acc.id, user_id="user-1")
        )
    assert exc.value.code == "ACCOUNT_LAST_ACTIVE"


async def test_archive_with_balance_blocked():
    repo = FakeAccountRepository(
        [
            _account(name="Con saldo", initial_balance=Decimal("100.00")),
            _account(name="Otra"),
        ]
    )
    acc = next(a for a in repo.store.values() if a.name == "Con saldo")
    with pytest.raises(BusinessRuleError) as exc:
        await ArchiveAccountUseCase(repo).execute(
            ArchiveAccountInput(account_id=acc.id, user_id="user-1")
        )
    assert exc.value.code == "ACCOUNT_HAS_BALANCE"


async def test_archive_forbidden_for_other_user():
    repo = FakeAccountRepository([_account(name="A"), _account(name="B")])
    acc = next(a for a in repo.store.values() if a.name == "A")
    with pytest.raises(BusinessRuleError):
        await ArchiveAccountUseCase(repo).execute(
            ArchiveAccountInput(account_id=acc.id, user_id="other")
        )


# ---------- restore ----------


async def test_restore_recovers_original_name():
    repo = FakeAccountRepository(
        [
            _account(name="Ahorros"),
            _account(name="Sueldo"),
        ]
    )
    acc = next(a for a in repo.store.values() if a.name == "Ahorros")
    await ArchiveAccountUseCase(repo).execute(
        ArchiveAccountInput(account_id=acc.id, user_id="user-1")
    )
    out = await RestoreAccountUseCase(repo).execute(
        RestoreAccountInput(account_id=acc.id, user_id="user-1")
    )
    assert out.name == "Ahorros"
    assert out.status == "ACTIVE"


async def test_restore_name_collision_conflict():
    repo = FakeAccountRepository(
        [
            _account(name="Ahorros"),
            _account(name="Sueldo"),
        ]
    )
    acc = next(a for a in repo.store.values() if a.name == "Ahorros")
    await ArchiveAccountUseCase(repo).execute(
        ArchiveAccountInput(account_id=acc.id, user_id="user-1")
    )
    # Alguien recrea el nombre mientras tanto (caso WhatsApp).
    repo.store["new-id"] = _account(name="Ahorros")
    with pytest.raises(ConflictError):
        await RestoreAccountUseCase(repo).execute(
            RestoreAccountInput(account_id=acc.id, user_id="user-1")
        )


async def test_restore_active_account_rejected():
    repo = FakeAccountRepository([_account(name="A"), _account(name="B")])
    acc = next(a for a in repo.store.values() if a.name == "A")
    with pytest.raises(BusinessRuleError) as exc:
        await RestoreAccountUseCase(repo).execute(
            RestoreAccountInput(account_id=acc.id, user_id="user-1")
        )
    assert exc.value.code == "ACCOUNT_NOT_ARCHIVED"


# ---------- get / list ownership ----------


async def test_get_allows_owner_and_admin():
    repo = FakeAccountRepository([_account(name="A")])
    acc = next(iter(repo.store.values()))
    out = await GetAccountUseCase(repo).execute(
        GetAccountInput(account_id=acc.id, requester_id="user-1")
    )
    assert out.id == acc.id
    out_admin = await GetAccountUseCase(repo).execute(
        GetAccountInput(
            account_id=acc.id, requester_id="admin-1", requester_role="ADMIN"
        )
    )
    assert out_admin.id == acc.id
    with pytest.raises(BusinessRuleError):
        await GetAccountUseCase(repo).execute(
            GetAccountInput(account_id=acc.id, requester_id="other")
        )


async def test_get_not_found():
    with pytest.raises(NotFoundError):
        await GetAccountUseCase(FakeAccountRepository()).execute(
            GetAccountInput(account_id="missing", requester_id="user-1")
        )


async def test_list_filters_archived_by_default():
    active = _account(name="Activa")
    archived = _account(name="Vieja").archive_with_shadow_name()
    repo = FakeAccountRepository([active, archived])
    uc = ListAccountsByUserUseCase(repo)
    result = await uc.execute(
        ListAccountsByUserInput(user_id="user-1", requester_id="user-1")
    )
    assert [r.name for r in result] == ["Activa"]
    result_all = await uc.execute(
        ListAccountsByUserInput(
            user_id="user-1", requester_id="user-1", include_archived=True
        )
    )
    assert len(result_all) == 2


async def test_list_forbidden_for_other_user():
    repo = FakeAccountRepository([_account(name="A")])
    with pytest.raises(BusinessRuleError):
        await ListAccountsByUserUseCase(repo).execute(
            ListAccountsByUserInput(user_id="user-1", requester_id="other")
        )


# ---------- entity shadow helpers ----------


def test_shadow_name_truncates_to_80():
    long_name = "x" * 80
    acc = _account(name=long_name).archive_with_shadow_name()
    assert len(acc.name) <= 80
    assert "_deleted_" in acc.name
    assert acc.is_default is False


def test_restore_entity_rejects_active():
    acc = _account(name="A")
    with pytest.raises(BusinessRuleError):
        acc.restore("A")


# ---------- controller ----------


async def test_controller_create_conflict_rolls_back():
    repo = FakeAccountRepository([_account(name="Ahorros")])
    session = FakeSession()
    controller = AccountController(repo, session)
    with pytest.raises(HTTPException) as exc:
        await controller.create(CreateAccountInput(user_id="user-1", name="Ahorros"))
    assert exc.value.status_code == 409
    assert session.rollbacks == 1
    assert session.commits == 0


async def test_controller_archive_forbidden_maps_403():
    repo = FakeAccountRepository([_account(name="A"), _account(name="B")])
    session = FakeSession()
    controller = AccountController(repo, session)
    acc = next(a for a in repo.store.values() if a.name == "A")
    with pytest.raises(HTTPException) as exc:
        await controller.archive(
            ArchiveAccountInput(account_id=acc.id, user_id="other")
        )
    assert exc.value.status_code == 403


async def test_controller_archive_last_active_maps_409():
    repo = FakeAccountRepository([_account(name="Única")])
    session = FakeSession()
    controller = AccountController(repo, session)
    acc = next(iter(repo.store.values()))
    with pytest.raises(HTTPException) as exc:
        await controller.archive(
            ArchiveAccountInput(account_id=acc.id, user_id="user-1")
        )
    assert exc.value.status_code == 409
    assert exc.value.detail["code"] == "ACCOUNT_LAST_ACTIVE"


async def test_controller_get_not_found_maps_404():
    controller = AccountController(FakeAccountRepository(), FakeSession())
    with pytest.raises(HTTPException) as exc:
        await controller.get(
            GetAccountInput(account_id="missing", requester_id="user-1")
        )
    assert exc.value.status_code == 404
