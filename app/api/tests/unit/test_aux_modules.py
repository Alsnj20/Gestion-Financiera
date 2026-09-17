"""Unit tests for PaymentMethods/Notifications/Recurring/Audit/Conversations."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from fastapi import HTTPException

from modules.audit_logs.application.use_cases.create_audit_log import (
    CreateAuditLogInput,
    CreateAuditLogUseCase,
)
from modules.audit_logs.domain.entities.audit_log import AuditLog
from modules.audit_logs.presentation.controllers.audit_log_controller import (
    AuditLogController,
)
from modules.conversations.application.use_cases.create_conversation_message import (
    CreateConversationMessageInput,
    CreateConversationMessageUseCase,
)
from modules.conversations.domain.entities.conversation_message import ConversationMessage
from modules.conversations.presentation.controllers.conversation_message_controller import (
    ConversationMessageController,
)
from modules.notifications.application.use_cases.cancel_notification import (
    CancelNotificationInput,
    CancelNotificationUseCase,
)
from modules.notifications.application.use_cases.create_notification import (
    CreateNotificationInput,
    CreateNotificationUseCase,
)
from modules.notifications.application.use_cases.send_notification import (
    SendNotificationInput,
    SendNotificationUseCase,
)
from modules.notifications.domain.entities.notification import Notification
from modules.notifications.presentation.controllers.notification_controller import (
    NotificationController,
)
from modules.payment_methods.application.use_cases.archive_payment_method import (
    ArchivePaymentMethodInput,
    ArchivePaymentMethodUseCase,
)
from modules.payment_methods.application.use_cases.create_payment_method import (
    CreatePaymentMethodInput,
    CreatePaymentMethodUseCase,
)
from modules.payment_methods.domain.entities.payment_method import PaymentMethod
from modules.payment_methods.presentation.controllers.payment_method_controller import (
    PaymentMethodController,
)
from modules.recurring_expenses.application.use_cases.cancel_recurring_expense import (
    CancelRecurringExpenseInput,
    CancelRecurringExpenseUseCase,
)
from modules.recurring_expenses.application.use_cases.create_recurring_expense import (
    CreateRecurringExpenseInput,
    CreateRecurringExpenseUseCase,
)
from modules.recurring_expenses.application.use_cases.pause_recurring_expense import (
    PauseRecurringExpenseInput,
    PauseRecurringExpenseUseCase,
)
from modules.recurring_expenses.domain.entities.recurring_expense import RecurringExpense
from modules.recurring_expenses.presentation.controllers.recurring_expense_controller import (
    RecurringExpenseController,
)
from shared.errors import BusinessRuleError, ValidationError
from shared.types.enums import NotificationStatus, RecurringStatus


class FakeRepo:
    def __init__(self, items=None) -> None:
        self.store: dict = {x.id: x for x in (items or [])}

    async def save(self, item) -> None:
        self.store[item.id] = item

    async def find_by_id(self, item_id: str, **kwargs):
        return self.store.get(item_id)

    async def find_by_user(self, user_id: str):
        return [x for x in self.store.values() if x.user_id == user_id]


class FakePmRepo(FakeRepo):
    async def find_by_account(self, account_id: str):
        return [x for x in self.store.values() if x.account_id == account_id]

    async def clear_default_for_user(self, user_id: str) -> None:
        for x in self.store.values():
            if x.user_id == user_id and x.is_default:
                self.store[x.id] = x.unmark_as_default()

    async def exists_name_for_user(self, user_id: str, name: str) -> bool:
        return any(
            x for x in self.store.values() if x.user_id == user_id and x.name == name.strip()
        )


class FakeAccountRepo:
    def __init__(self, accounts=None) -> None:
        self.store: dict = {a.id: a for a in (accounts or [])}

    async def save(self, a) -> None:
        self.store[a.id] = a

    async def find_by_id(self, i: str, **kwargs):
        return self.store.get(i)


class FakeSession:
    async def commit(self) -> None:
        pass

    async def rollback(self) -> None:
        pass


def _account(**kwargs):
    from modules.accounts.domain.entities.account import Account

    base = {"user_id": "user-1", "name": "Caja"}
    base.update(kwargs)
    return Account.create(**base)


# ---------- payment_methods ----------


async def test_pm_rejects_foreign_account():
    from modules.accounts.domain.entities.account import Account

    foreign = Account.create(user_id="other", name="Ajena")
    acc_repo = FakeAccountRepo([foreign])
    with pytest.raises(BusinessRuleError) as exc:
        await CreatePaymentMethodUseCase(FakePmRepo(), acc_repo).execute(
            CreatePaymentMethodInput(user_id="user-1", account_id=foreign.id, name="TC")
        )
    assert exc.value.code == "FORBIDDEN"


async def test_pm_default_clears_others_and_archive_shadow():
    acc = _account()
    acc_repo = FakeAccountRepo([acc])
    repo = FakePmRepo()
    ctl = PaymentMethodController(repo, acc_repo, FakeSession())
    first = await ctl.create(
        CreatePaymentMethodInput(
            user_id="user-1", account_id=acc.id, name="TC", is_default=True
        )
    )
    second = await ctl.create(
        CreatePaymentMethodInput(
            user_id="user-1", account_id=acc.id, name="Cash", is_default=True
        )
    )
    assert repo.store[first["id"]].is_default is False
    assert repo.store[second["id"]].is_default is True

    await ctl.archive(ArchivePaymentMethodInput(pm_id=second["id"], user_id="user-1"))
    saved = repo.store[second["id"]]
    assert saved.status.value == "ARCHIVED"
    assert saved.is_default is False
    assert saved.name.startswith("Cash_deleted_")


async def test_pm_strict_bool():
    with pytest.raises(ValidationError) as exc:
        PaymentMethod.create(user_id="u", account_id="a", name="n", is_default="yes")  # type: ignore[arg-type]
    assert exc.value.code == "PM_IS_DEFAULT_INVALID"


# ---------- notifications ----------


def _notif(**kwargs) -> Notification:
    base = {"user_id": "user-1", "title": "T", "message": "M"}
    base.update(kwargs)
    return Notification.create(**base)


async def test_notification_send_and_freeze():
    repo = FakeRepo([_notif()])
    n = next(iter(repo.store.values()))
    ctl = NotificationController(repo, FakeSession())
    sent = await ctl.send(SendNotificationInput(notification_id=n.id, user_id="user-1"))
    assert sent["status"] == "SENT"
    assert sent["sent_at"] is not None
    # Lo enviado no se reescribe.
    with pytest.raises(HTTPException) as exc:
        await ctl.cancel(CancelNotificationInput(notification_id=n.id, user_id="user-1"))
    assert exc.value.detail["code"] == "NOTIF_NOT_PENDING"


async def test_notification_update_only_pending():
    from modules.notifications.application.use_cases.update_notification import (
        UpdateNotificationInput,
    )

    repo = FakeRepo([_notif()])
    n = next(iter(repo.store.values()))
    ctl = NotificationController(repo, FakeSession())
    out = await ctl.update(
        UpdateNotificationInput(notification_id=n.id, user_id="user-1", title="Nuevo")
    )
    assert out["title"] == "Nuevo"
    await ctl.send(SendNotificationInput(notification_id=n.id, user_id="user-1"))
    with pytest.raises(HTTPException) as exc:
        await ctl.update(
            UpdateNotificationInput(notification_id=n.id, user_id="user-1", title="X")
        )
    assert exc.value.detail["code"] == "NOTIF_NOT_PENDING"


# ---------- recurring ----------


async def test_recurring_pause_resume_cancel():
    acc = _account()
    repo = FakeRepo()
    ctl = RecurringExpenseController(repo, FakeAccountRepo([acc]), FakeRepo(), FakeSession())
    out = await ctl.create(
        CreateRecurringExpenseInput(
            user_id="user-1",
            account_id=acc.id,
            amount=Decimal("50.00"),
            next_date=date(2026, 3, 1),
        )
    )
    assert out["status"] == "ACTIVE"
    paused = await ctl.pause(PauseRecurringExpenseInput(re_id=out["id"], user_id="user-1"))
    assert paused["status"] == "PAUSED"
    cancelled = await ctl.cancel(
        CancelRecurringExpenseInput(re_id=out["id"], user_id="user-1")
    )
    assert cancelled["status"] == "CANCELLED"
    assert repo.store[out["id"]].status == RecurringStatus.CANCELLED


async def test_recurring_rejects_foreign_account():
    from modules.accounts.domain.entities.account import Account

    foreign = Account.create(user_id="other", name="Ajena")
    repo = FakeRepo()
    ctl = RecurringExpenseController(repo, FakeAccountRepo([foreign]), FakeRepo(), FakeSession())
    with pytest.raises(HTTPException) as exc:
        await ctl.create(
            CreateRecurringExpenseInput(
                user_id="user-1",
                account_id=foreign.id,
                amount=Decimal("10.00"),
                next_date=date(2026, 3, 1),
            )
        )
    assert exc.value.detail["code"] == "FORBIDDEN"


# ---------- audit (append-only) ----------


async def test_audit_create_and_list():
    repo = FakeRepo()
    ctl = AuditLogController(repo, FakeSession())
    out = await ctl.create(
        CreateAuditLogInput(
            user_id="user-1", entity_type="account", entity_id="a-1", action="CREATE"
        )
    )
    assert out["action"] == "CREATE"
    assert repo.store[out["id"]].source == "MANUAL"


async def test_audit_has_no_delete_or_update():
    import modules.audit_logs.application.ports.audit_log_repository as port
    import modules.audit_logs.presentation.router as router

    assert not hasattr(port.AuditLogRepositoryPort, "delete")
    routes = {(r.path, tuple(r.methods or [])) for r in router.router.routes}
    assert not any("DELETE" in methods or "PUT" in methods for _, methods in routes)


# ---------- conversations (append-only + confidence) ----------


async def test_conversation_create_and_confidence_guard():
    repo = FakeRepo()
    ctl = ConversationMessageController(repo, FakeSession())
    from modules.conversations.application.use_cases.create_conversation_message import (
        CreateConversationMessageInput,
    )

    out = await ctl.create(
        CreateConversationMessageInput(
            user_id="user-1", external_message_id="wa-1", content="hola", confidence=0.9
        )
    )
    assert out["external_message_id"] == "wa-1"
    with pytest.raises(ValidationError) as exc:
        ConversationMessage.create(user_id="u", external_message_id="x", confidence=1.5)
    assert exc.value.code == "CM_CONFIDENCE_OUT_OF_RANGE"


async def test_conversations_has_no_delete_or_update():
    import modules.conversations.application.ports.conversation_message_repository as port
    import modules.conversations.presentation.router as router

    assert not hasattr(port.ConversationMessageRepositoryPort, "delete")
    routes = {(r.path, tuple(r.methods or [])) for r in router.router.routes}
    assert not any("DELETE" in methods or "PUT" in methods for _, methods in routes)
