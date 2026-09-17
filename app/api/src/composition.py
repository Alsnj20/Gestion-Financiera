from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.session import get_session
from modules.accounts.infrastructure.adapters.sqlalchemy_account_repository import (
    SqlAlchemyAccountRepository,
)
from modules.accounts.presentation.controllers.account_controller import (
    AccountController,
)
from modules.audit_logs.application.use_cases.create_audit_log import (
    CreateAuditLogUseCase,
)
from modules.audit_logs.infrastructure.adapters.sqlalchemy_audit_log_repository import (
    SqlAlchemyAuditLogRepository,
)
from modules.auth.infrastructure.adapters.sqlalchemy_otp_repository import (
    SqlAlchemyOtpRepository,
)
from modules.auth.infrastructure.adapters.sqlalchemy_refresh_session_repository import (
    SqlAlchemyRefreshSessionRepository,
)
from modules.auth.infrastructure.adapters.sqlalchemy_whatsapp_link_repository import (
    SqlAlchemyWhatsAppLinkRepository,
)
from modules.auth.infrastructure.otp_senders import DevelopmentOtpSender, NullOtpSender
from modules.auth.presentation.controllers.auth_controller import AuthController
from modules.budgets.infrastructure.adapters.sqlalchemy_budget_repository import (
    SqlAlchemyBudgetRepository,
)
from modules.budgets.presentation.controllers.budget_controller import BudgetController
from modules.categories.infrastructure.adapters.sqlalchemy_category_repository import (
    SqlAlchemyCategoryRepository,
)
from modules.categories.presentation.controllers.category_controller import (
    CategoryController,
)
from modules.conversations.application.use_cases.create_conversation_message import (
    CreateConversationMessageUseCase,
)
from modules.conversations.infrastructure.adapters.sqlalchemy_conversation_message_repository import (
    SqlAlchemyConversationMessageRepository,
)
from modules.debts.infrastructure.adapters.sqlalchemy_debt_repository import (
    SqlAlchemyDebtRepository,
)
from modules.debts.presentation.controllers.debt_controller import DebtController
from modules.limits.infrastructure.adapters.sqlalchemy_limit_repository import (
    SqlAlchemyLimitRepository,
)
from modules.limits.presentation.controllers.limit_controller import LimitController
from modules.loans.infrastructure.adapters.sqlalchemy_loan_repository import (
    SqlAlchemyLoanRepository,
)
from modules.loans.presentation.controllers.loan_controller import LoanController
from modules.notifications.application.use_cases.create_notification import (
    CreateNotificationUseCase,
)
from modules.notifications.infrastructure.adapters.sqlalchemy_notification_repository import (
    SqlAlchemyNotificationRepository,
)
from modules.payment_methods.application.use_cases.create_payment_method import (
    CreatePaymentMethodUseCase,
)
from modules.payment_methods.infrastructure.adapters.sqlalchemy_payment_method_repository import (
    SqlAlchemyPaymentMethodRepository,
)
from modules.recurring_expenses.application.use_cases.create_recurring_expense import (
    CreateRecurringExpenseUseCase,
)
from modules.recurring_expenses.infrastructure.adapters.sqlalchemy_recurring_expense_repository import (
    SqlAlchemyRecurringExpenseRepository,
)
from modules.tags.infrastructure.adapters.sqlalchemy_tag_repository import (
    SqlAlchemyTagRepository,
)
from modules.tags.presentation.controllers.tag_controller import TagController
from modules.transactions.infrastructure.adapters.sqlalchemy_transaction_repository import (
    SqlAlchemyTransactionRepository,
)
from modules.transactions.presentation.controllers.transaction_controller import (
    TransactionController,
)
from modules.transfers.infrastructure.adapters.sqlalchemy_transfer_repository import (
    SqlAlchemyTransferRepository,
)
from modules.transfers.presentation.controllers.transfer_controller import (
    TransferController,
)
from modules.users.infrastructure.adapters.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from modules.users.presentation.controllers.user_controller import UserController
from shared.settings import settings


# ---- Auth ----
def build_otp_sender() -> DevelopmentOtpSender | NullOtpSender:
    """Provider según configuración (D8): dev registra en DEBUG, prod exige real."""
    if settings.otp_sender_name == "log":
        return DevelopmentOtpSender()
    return NullOtpSender()


def build_auth_controller(session: AsyncSession) -> AuthController:
    return AuthController(
        SqlAlchemyOtpRepository(session),
        SqlAlchemyWhatsAppLinkRepository(session),
        SqlAlchemyUserRepository(session),
        SqlAlchemyRefreshSessionRepository(session),
        build_otp_sender(),
        session,
    )


def get_auth_controller(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AuthController:
    """Dependencia FastAPI — inyecta el controller sin acoplar el router a infra."""
    return build_auth_controller(session)


# ---- Users ----
def build_user_repository(session: AsyncSession) -> SqlAlchemyUserRepository:
    return SqlAlchemyUserRepository(session)


def build_user_controller(session: AsyncSession) -> UserController:
    return UserController(SqlAlchemyUserRepository(session), session)


def get_user_controller(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UserController:
    """Dependencia FastAPI — inyecta el controller sin acoplar el router a infra."""
    return build_user_controller(session)


# ---- Accounts ----
def build_account_controller(session: AsyncSession) -> AccountController:
    return AccountController(SqlAlchemyAccountRepository(session), session)


def get_account_controller(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AccountController:
    """Dependencia FastAPI — inyecta el controller sin acoplar el router a infra."""
    return build_account_controller(session)


# ---- Transactions ----
def build_transaction_controller(session: AsyncSession) -> TransactionController:
    return TransactionController(
        SqlAlchemyTransactionRepository(session),
        SqlAlchemyAccountRepository(session),
        session,
    )


def get_transaction_controller(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TransactionController:
    """Dependencia FastAPI — inyecta el controller sin acoplar el router a infra."""
    return build_transaction_controller(session)


# ---- Categories ----
def build_category_controller(session: AsyncSession) -> CategoryController:
    return CategoryController(SqlAlchemyCategoryRepository(session), session)


def get_category_controller(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CategoryController:
    """Dependencia FastAPI — inyecta el controller sin acoplar el router a infra."""
    return build_category_controller(session)


# ---- Tags ----
def build_tag_controller(session: AsyncSession) -> TagController:
    return TagController(SqlAlchemyTagRepository(session), session)


def get_tag_controller(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TagController:
    """Dependencia FastAPI — inyecta el controller sin acoplar el router a infra."""
    return build_tag_controller(session)


# ---- Payment Methods ----
def build_create_payment_method_use_case(
    session: AsyncSession,
) -> CreatePaymentMethodUseCase:
    return CreatePaymentMethodUseCase(SqlAlchemyPaymentMethodRepository(session))


def build_payment_method_repository(
    session: AsyncSession,
) -> SqlAlchemyPaymentMethodRepository:
    return SqlAlchemyPaymentMethodRepository(session)


# ---- Budgets ----
def build_budget_controller(session: AsyncSession) -> BudgetController:
    return BudgetController(
        SqlAlchemyBudgetRepository(session),
        SqlAlchemyCategoryRepository(session),
        session,
    )


def get_budget_controller(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> BudgetController:
    """Dependencia FastAPI — inyecta el controller sin acoplar el router a infra."""
    return build_budget_controller(session)


# ---- Limits ----
def build_limit_controller(session: AsyncSession) -> LimitController:
    return LimitController(
        SqlAlchemyLimitRepository(session),
        SqlAlchemyCategoryRepository(session),
        session,
    )


def get_limit_controller(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> LimitController:
    """Dependencia FastAPI — inyecta el controller sin acoplar el router a infra."""
    return build_limit_controller(session)


# ---- Notifications ----
def build_create_notification_use_case(
    session: AsyncSession,
) -> CreateNotificationUseCase:
    return CreateNotificationUseCase(SqlAlchemyNotificationRepository(session))


def build_notification_repository(
    session: AsyncSession,
) -> SqlAlchemyNotificationRepository:
    return SqlAlchemyNotificationRepository(session)


# ---- Transfers ----
def build_transfer_controller(session: AsyncSession) -> TransferController:
    return TransferController(
        SqlAlchemyTransferRepository(session),
        SqlAlchemyTransactionRepository(session),
        SqlAlchemyAccountRepository(session),
        session,
    )


def get_transfer_controller(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TransferController:
    """Dependencia FastAPI — inyecta el controller sin acoplar el router a infra."""
    return build_transfer_controller(session)


# ---- Loans ----
def build_loan_controller(session: AsyncSession) -> LoanController:
    return LoanController(
        SqlAlchemyLoanRepository(session),
        SqlAlchemyTransactionRepository(session),
        SqlAlchemyAccountRepository(session),
        session,
    )


def get_loan_controller(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> LoanController:
    """Dependencia FastAPI — inyecta el controller sin acoplar el router a infra."""
    return build_loan_controller(session)


# ---- Debts ----
def build_debt_controller(session: AsyncSession) -> DebtController:
    return DebtController(
        SqlAlchemyDebtRepository(session),
        SqlAlchemyTransactionRepository(session),
        SqlAlchemyAccountRepository(session),
        session,
    )


def get_debt_controller(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> DebtController:
    """Dependencia FastAPI — inyecta el controller sin acoplar el router a infra."""
    return build_debt_controller(session)


# ---- Recurring Expenses ----
def build_create_recurring_expense_use_case(
    session: AsyncSession,
) -> CreateRecurringExpenseUseCase:
    return CreateRecurringExpenseUseCase(SqlAlchemyRecurringExpenseRepository(session))


def build_recurring_expense_repository(
    session: AsyncSession,
) -> SqlAlchemyRecurringExpenseRepository:
    return SqlAlchemyRecurringExpenseRepository(session)


# ---- Audit Logs ----
def build_create_audit_log_use_case(session: AsyncSession) -> CreateAuditLogUseCase:
    return CreateAuditLogUseCase(SqlAlchemyAuditLogRepository(session))


def build_audit_log_repository(session: AsyncSession) -> SqlAlchemyAuditLogRepository:
    return SqlAlchemyAuditLogRepository(session)


# ---- Conversations ----
def build_create_conversation_message_use_case(
    session: AsyncSession,
) -> CreateConversationMessageUseCase:
    return CreateConversationMessageUseCase(
        SqlAlchemyConversationMessageRepository(session)
    )


def build_conversation_message_repository(
    session: AsyncSession,
) -> SqlAlchemyConversationMessageRepository:
    return SqlAlchemyConversationMessageRepository(session)
