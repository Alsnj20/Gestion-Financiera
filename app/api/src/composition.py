from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from modules.users.infrastructure.adapters.sqlalchemy_user_repository import SqlAlchemyUserRepository

from modules.accounts.application.use_cases.create_account import CreateAccountUseCase
from modules.accounts.infrastructure.repositories.sqlalchemy_account_repository import SqlAlchemyAccountRepository

from modules.transactions.application.use_cases.create_transaction import CreateTransactionUseCase
from modules.transactions.infrastructure.adapters.sqlalchemy_transaction_repository import SqlAlchemyTransactionRepository

from modules.categories.application.use_cases.create_category import CreateCategoryUseCase
from modules.categories.infrastructure.adapters.sqlalchemy_category_repository import SqlAlchemyCategoryRepository

from modules.tags.application.use_cases.create_tag import CreateTagUseCase
from modules.tags.infrastructure.adapters.sqlalchemy_tag_repository import SqlAlchemyTagRepository

from modules.payment_methods.application.use_cases.create_payment_method import CreatePaymentMethodUseCase
from modules.payment_methods.infrastructure.adapters.sqlalchemy_payment_method_repository import SqlAlchemyPaymentMethodRepository

from modules.budgets.application.use_cases.create_budget import CreateBudgetUseCase
from modules.budgets.infrastructure.adapters.sqlalchemy_budget_repository import SqlAlchemyBudgetRepository

from modules.limits.application.use_cases.create_limit import CreateLimitUseCase
from modules.limits.infrastructure.adapters.sqlalchemy_limit_repository import SqlAlchemyLimitRepository

from modules.notifications.application.use_cases.create_notification import CreateNotificationUseCase
from modules.notifications.infrastructure.adapters.sqlalchemy_notification_repository import SqlAlchemyNotificationRepository

from modules.transfers.application.use_cases.create_transfer import CreateTransferUseCase
from modules.transfers.infrastructure.adapters.sqlalchemy_transfer_repository import SqlAlchemyTransferRepository

from modules.loans.application.use_cases.create_loan import CreateLoanUseCase
from modules.loans.infrastructure.adapters.sqlalchemy_loan_repository import SqlAlchemyLoanRepository

from modules.debts.application.use_cases.create_debt import CreateDebtUseCase
from modules.debts.infrastructure.adapters.sqlalchemy_debt_repository import SqlAlchemyDebtRepository

from modules.recurring_expenses.application.use_cases.create_recurring_expense import CreateRecurringExpenseUseCase
from modules.recurring_expenses.infrastructure.adapters.sqlalchemy_recurring_expense_repository import SqlAlchemyRecurringExpenseRepository

from modules.audit_logs.application.use_cases.create_audit_log import CreateAuditLogUseCase
from modules.audit_logs.infrastructure.adapters.sqlalchemy_audit_log_repository import SqlAlchemyAuditLogRepository

from modules.conversations.application.use_cases.create_conversation_message import CreateConversationMessageUseCase
from modules.conversations.infrastructure.adapters.sqlalchemy_conversation_message_repository import SqlAlchemyConversationMessageRepository


# ---- Users ----
def build_user_repository(session: AsyncSession) -> SqlAlchemyUserRepository:
    return SqlAlchemyUserRepository(session)


# ---- Accounts ----
def build_create_account_use_case(session: AsyncSession) -> CreateAccountUseCase:
    return CreateAccountUseCase(SqlAlchemyAccountRepository(session))

def build_account_repository(session: AsyncSession) -> SqlAlchemyAccountRepository:
    return SqlAlchemyAccountRepository(session)


# ---- Transactions ----
def build_create_transaction_use_case(session: AsyncSession) -> CreateTransactionUseCase:
    return CreateTransactionUseCase(
        SqlAlchemyTransactionRepository(session),
        SqlAlchemyAccountRepository(session),
    )

def build_transaction_repository(session: AsyncSession) -> SqlAlchemyTransactionRepository:
    return SqlAlchemyTransactionRepository(session)


# ---- Categories ----
def build_create_category_use_case(session: AsyncSession) -> CreateCategoryUseCase:
    return CreateCategoryUseCase(SqlAlchemyCategoryRepository(session))

def build_category_repository(session: AsyncSession) -> SqlAlchemyCategoryRepository:
    return SqlAlchemyCategoryRepository(session)


# ---- Tags ----
def build_create_tag_use_case(session: AsyncSession) -> CreateTagUseCase:
    return CreateTagUseCase(SqlAlchemyTagRepository(session))

def build_tag_repository(session: AsyncSession) -> SqlAlchemyTagRepository:
    return SqlAlchemyTagRepository(session)


# ---- Payment Methods ----
def build_create_payment_method_use_case(session: AsyncSession) -> CreatePaymentMethodUseCase:
    return CreatePaymentMethodUseCase(SqlAlchemyPaymentMethodRepository(session))

def build_payment_method_repository(session: AsyncSession) -> SqlAlchemyPaymentMethodRepository:
    return SqlAlchemyPaymentMethodRepository(session)


# ---- Budgets ----
def build_create_budget_use_case(session: AsyncSession) -> CreateBudgetUseCase:
    return CreateBudgetUseCase(SqlAlchemyBudgetRepository(session))

def build_budget_repository(session: AsyncSession) -> SqlAlchemyBudgetRepository:
    return SqlAlchemyBudgetRepository(session)


# ---- Limits ----
def build_create_limit_use_case(session: AsyncSession) -> CreateLimitUseCase:
    return CreateLimitUseCase(SqlAlchemyLimitRepository(session))

def build_limit_repository(session: AsyncSession) -> SqlAlchemyLimitRepository:
    return SqlAlchemyLimitRepository(session)


# ---- Notifications ----
def build_create_notification_use_case(session: AsyncSession) -> CreateNotificationUseCase:
    return CreateNotificationUseCase(SqlAlchemyNotificationRepository(session))

def build_notification_repository(session: AsyncSession) -> SqlAlchemyNotificationRepository:
    return SqlAlchemyNotificationRepository(session)


# ---- Transfers ----
def build_create_transfer_use_case(session: AsyncSession) -> CreateTransferUseCase:
    return CreateTransferUseCase(
        SqlAlchemyTransferRepository(session),
        SqlAlchemyTransactionRepository(session),
        SqlAlchemyAccountRepository(session),
    )


# ---- Loans ----
def build_create_loan_use_case(session: AsyncSession) -> CreateLoanUseCase:
    return CreateLoanUseCase(SqlAlchemyLoanRepository(session))

def build_loan_repository(session: AsyncSession) -> SqlAlchemyLoanRepository:
    return SqlAlchemyLoanRepository(session)


# ---- Debts ----
def build_create_debt_use_case(session: AsyncSession) -> CreateDebtUseCase:
    return CreateDebtUseCase(SqlAlchemyDebtRepository(session))

def build_debt_repository(session: AsyncSession) -> SqlAlchemyDebtRepository:
    return SqlAlchemyDebtRepository(session)


# ---- Recurring Expenses ----
def build_create_recurring_expense_use_case(session: AsyncSession) -> CreateRecurringExpenseUseCase:
    return CreateRecurringExpenseUseCase(SqlAlchemyRecurringExpenseRepository(session))

def build_recurring_expense_repository(session: AsyncSession) -> SqlAlchemyRecurringExpenseRepository:
    return SqlAlchemyRecurringExpenseRepository(session)


# ---- Audit Logs ----
def build_create_audit_log_use_case(session: AsyncSession) -> CreateAuditLogUseCase:
    return CreateAuditLogUseCase(SqlAlchemyAuditLogRepository(session))

def build_audit_log_repository(session: AsyncSession) -> SqlAlchemyAuditLogRepository:
    return SqlAlchemyAuditLogRepository(session)


# ---- Conversations ----
def build_create_conversation_message_use_case(session: AsyncSession) -> CreateConversationMessageUseCase:
    return CreateConversationMessageUseCase(SqlAlchemyConversationMessageRepository(session))

def build_conversation_message_repository(session: AsyncSession) -> SqlAlchemyConversationMessageRepository:
    return SqlAlchemyConversationMessageRepository(session)
