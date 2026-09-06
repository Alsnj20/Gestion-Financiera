"""Modelos SQLAlchemy — capa infraestructura. Defensivos: sin nulls innecesarios, defaults seguros."""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from infrastructure.database.base import Base

# Helpers
UUID_PK = lambda: mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
STR_120 = String(120)
STR_80 = String(80)
STR_60 = String(60)
STR_40 = String(40)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ---------- User ----------
class UserModel(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("email = '' OR email LIKE '%@%.%'", name="ck_users_email_valid"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(STR_120, nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, default="", server_default="")
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False, default="", server_default="")
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="America/Lima", server_default="America/Lima")
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="PEN", server_default="PEN")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    accounts: Mapped[list[AccountModel]] = relationship(back_populates="user", cascade="all, delete-orphan")


# ---------- Account ----------
class AccountModel(Base):
    __tablename__ = "accounts"
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_accounts_user_name"),
        CheckConstraint("length(name) > 0", name="ck_accounts_name_not_empty"),
        CheckConstraint("current_balance >= -999999999999.99", name="ck_accounts_balance_range"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(STR_80, nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False, default="OTHER", server_default="OTHER")
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="PEN", server_default="PEN")
    initial_balance: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0, server_default="0")
    current_balance: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0, server_default="0")
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE", server_default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    user: Mapped[UserModel] = relationship(back_populates="accounts")
    payment_methods: Mapped[list[PaymentMethodModel]] = relationship(back_populates="account", cascade="all, delete-orphan")


# ---------- PaymentMethod ----------
class PaymentMethodModel(Base):
    __tablename__ = "payment_methods"
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_payment_methods_user_name"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(STR_60, nullable=False)
    type: Mapped[str] = mapped_column(String(60), nullable=False, default="", server_default="")
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE", server_default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    account: Mapped[AccountModel] = relationship(back_populates="payment_methods")


# ---------- Category ----------
class CategoryModel(Base):
    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint("user_id", "name", "parent_id", name="uq_categories_user_name_parent"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, default=None)  # null solo aquí representa raíz, mapeado a "" en dominio
    name: Mapped[str] = mapped_column(STR_80, nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False, default="BOTH", server_default="BOTH")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE", server_default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)


# ---------- Tag ----------
class TagModel(Base):
    __tablename__ = "tags"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_tags_user_name"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(STR_40, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)


# ---------- Transaction ----------
class TransactionModel(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_transactions_amount_positive"),
        Index("ix_transactions_user_date", "user_id", "transaction_date"),
        Index("ix_transactions_account", "account_id"),
        Index("ix_transactions_category", "category_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=False)
    payment_method_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("payment_methods.id", ondelete="SET NULL"), nullable=True, default=None)
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # INCOME/EXPENSE/TRANSFER
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="PEN", server_default="PEN")
    transaction_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    category_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, default=None)
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="MANUAL", server_default="MANUAL")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="COMPLETED", server_default="COMPLETED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    tags: Mapped[list[TagModel]] = relationship(secondary="transaction_tags")


class TransactionTagModel(Base):
    __tablename__ = "transaction_tags"

    transaction_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("transactions.id", ondelete="CASCADE"), primary_key=True)
    tag_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)


# ---------- Transfer ----------
class TransferModel(Base):
    __tablename__ = "transfers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    source_account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=False)
    destination_account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=False)
    source_transaction_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("transactions.id", ondelete="RESTRICT"), nullable=False, unique=True)
    destination_transaction_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("transactions.id", ondelete="RESTRICT"), nullable=False, unique=True)
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="PEN", server_default="PEN")
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)


# ---------- Loan ----------
class LoanModel(Base):
    __tablename__ = "loans"
    __table_args__ = (CheckConstraint("principal_amount > 0", name="ck_loans_principal_positive"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    borrower_name: Mapped[str] = mapped_column(STR_120, nullable=False, index=True)
    principal_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    interest_rate: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0, server_default="0")
    interest_rate_type: Mapped[str] = mapped_column(String(20), nullable=False, default="PERCENTAGE", server_default="PERCENTAGE")
    payment_frequency: Mapped[str] = mapped_column(String(20), nullable=False, default="MONTHLY", server_default="MONTHLY")
    installment_count: Mapped[int] = mapped_column(nullable=False, default=1, server_default="1")
    installment_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0, server_default="0")
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    first_due_date: Mapped[date] = mapped_column(Date, nullable=False)
    amortization_method: Mapped[str] = mapped_column(String(20), nullable=False, default="SIMPLE", server_default="SIMPLE")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE", server_default="ACTIVE")
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    installments: Mapped[list[LoanInstallmentModel]] = relationship(back_populates="loan", cascade="all, delete-orphan", order_by="LoanInstallmentModel.installment_number")


class LoanInstallmentModel(Base):
    __tablename__ = "loan_installments"
    __table_args__ = (UniqueConstraint("loan_id", "installment_number", name="uq_loan_installment_number"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    loan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("loans.id", ondelete="CASCADE"), nullable=False, index=True)
    installment_number: Mapped[int] = mapped_column(nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    principal_due: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0, server_default="0")
    interest_due: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0, server_default="0")
    total_due: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0, server_default="0")
    principal_paid: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0, server_default="0")
    interest_paid: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0, server_default="0")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING", server_default="PENDING")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    loan: Mapped[LoanModel] = relationship(back_populates="installments")


class LoanPaymentModel(Base):
    __tablename__ = "loan_payments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    loan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("loans.id", ondelete="CASCADE"), nullable=False, index=True)
    installment_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("loan_installments.id", ondelete="SET NULL"), nullable=True, default=None)
    transaction_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("transactions.id", ondelete="RESTRICT"), nullable=False, unique=True)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    principal_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0, server_default="0")
    interest_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0, server_default="0")
    total_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)


# ---------- Debt (mirror Loan) ----------
class DebtModel(Base):
    __tablename__ = "debts"
    __table_args__ = (CheckConstraint("principal_amount > 0", name="ck_debts_principal_positive"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    creditor_name: Mapped[str] = mapped_column(STR_120, nullable=False, index=True)
    principal_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    interest_rate: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0, server_default="0")
    interest_rate_type: Mapped[str] = mapped_column(String(20), nullable=False, default="PERCENTAGE", server_default="PERCENTAGE")
    payment_frequency: Mapped[str] = mapped_column(String(20), nullable=False, default="MONTHLY", server_default="MONTHLY")
    installment_count: Mapped[int] = mapped_column(nullable=False, default=1, server_default="1")
    installment_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0, server_default="0")
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    first_due_date: Mapped[date] = mapped_column(Date, nullable=False)
    amortization_method: Mapped[str] = mapped_column(String(20), nullable=False, default="SIMPLE", server_default="SIMPLE")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE", server_default="ACTIVE")
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    installments: Mapped[list[DebtInstallmentModel]] = relationship(back_populates="debt", cascade="all, delete-orphan", order_by="DebtInstallmentModel.installment_number")


class DebtInstallmentModel(Base):
    __tablename__ = "debt_installments"
    __table_args__ = (UniqueConstraint("debt_id", "installment_number", name="uq_debt_installment_number"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    debt_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("debts.id", ondelete="CASCADE"), nullable=False, index=True)
    installment_number: Mapped[int] = mapped_column(nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    principal_due: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0, server_default="0")
    interest_due: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0, server_default="0")
    total_due: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0, server_default="0")
    principal_paid: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0, server_default="0")
    interest_paid: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0, server_default="0")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING", server_default="PENDING")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    debt: Mapped[DebtModel] = relationship(back_populates="installments")


class DebtPaymentModel(Base):
    __tablename__ = "debt_payments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    debt_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("debts.id", ondelete="CASCADE"), nullable=False, index=True)
    installment_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("debt_installments.id", ondelete="SET NULL"), nullable=True, default=None)
    transaction_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("transactions.id", ondelete="RESTRICT"), nullable=False, unique=True)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    principal_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0, server_default="0")
    interest_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0, server_default="0")
    total_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)


# ---------- Budget ----------
class BudgetModel(Base):
    __tablename__ = "budgets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(STR_120, nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    category_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, default=None)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE", server_default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)


# ---------- Limit ----------
class LimitModel(Base):
    __tablename__ = "limits"
    __table_args__ = (CheckConstraint("amount > 0", name="ck_limits_amount_positive"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(STR_120, nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    period_type: Mapped[str] = mapped_column(String(20), nullable=False, default="MONTHLY", server_default="MONTHLY")
    category_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, default=None)
    threshold_warning: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=80, server_default="80")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE", server_default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)


# ---------- RecurringExpense ----------
class RecurringExpenseModel(Base):
    __tablename__ = "recurring_expenses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    category_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, default=None)
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    frequency: Mapped[str] = mapped_column(String(20), nullable=False, default="MONTHLY", server_default="MONTHLY")
    next_date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE", server_default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)


# ---------- Notification ----------
class NotificationModel(Base):
    __tablename__ = "notifications"
    __table_args__ = (Index("ix_notifications_user_scheduled", "user_id", "scheduled_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(40), nullable=False, default="GENERAL", server_default="GENERAL")
    title: Mapped[str] = mapped_column(String(200), nullable=False, default="", server_default="")
    message: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING", server_default="PENDING")
    related_entity_type: Mapped[str] = mapped_column(String(40), nullable=False, default="", server_default="")
    related_entity_id: Mapped[str] = mapped_column(String(80), nullable=False, default="", server_default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)


# ---------- ConversationMessage ----------
class ConversationMessageModel(Base):
    __tablename__ = "conversation_messages"
    __table_args__ = (UniqueConstraint("external_message_id", name="uq_conversation_external_id"), Index("ix_conversation_user_created", "user_id", "created_at"))

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(20), nullable=False, default="WHATSAPP", server_default="WHATSAPP")
    external_message_id: Mapped[str] = mapped_column(String(120), nullable=False)
    direction: Mapped[str] = mapped_column(String(20), nullable=False, default="INBOUND", server_default="INBOUND")
    content: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    parsed_intent: Mapped[str] = mapped_column(String(60), nullable=False, default="", server_default="")
    parsed_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    confidence: Mapped[float | None] = mapped_column(Numeric(4, 3), nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)


# ---------- AuditLog ----------
class AuditLogModel(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (Index("ix_audit_user_entity", "user_id", "entity_type", "entity_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(40), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(80), nullable=False)
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    old_value: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    new_value: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="MANUAL", server_default="MANUAL")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
