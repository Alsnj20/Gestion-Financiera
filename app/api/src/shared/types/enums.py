from __future__ import annotations

from enum import StrEnum


def _safe_enum[EnumT: StrEnum](
    value: object,
    enum_cls: type[EnumT],
    default: EnumT,
) -> EnumT:
    """Convierte un valor al enum indicado o devuelve su valor por defecto."""
    if value is None:
        return default

    if isinstance(value, enum_cls):
        return value

    try:
        normalized = str(value).strip().upper()
        return enum_cls(normalized)
    except (ValueError, AttributeError):
        return default


# --- Account ---
class AccountType(StrEnum):
    BANK = "BANK"
    CASH = "CASH"
    SAVINGS = "SAVINGS"
    CREDIT_CARD = "CREDIT_CARD"
    OTHER = "OTHER"

    @classmethod
    def safe(cls, value: object) -> AccountType:
        return _safe_enum(value, cls, cls.OTHER)


class AccountStatus(StrEnum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"

    @classmethod
    def safe(cls, value: object) -> AccountStatus:
        return _safe_enum(value, cls, cls.ACTIVE)


# --- Transaction ---
class TransactionType(StrEnum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"
    TRANSFER = "TRANSFER"

    @classmethod
    def safe(cls, value: object) -> TransactionType:
        return _safe_enum(value, cls, cls.EXPENSE)


class TransactionStatus(StrEnum):
    COMPLETED = "COMPLETED"
    PENDING = "PENDING"
    CANCELLED = "CANCELLED"

    @classmethod
    def safe(cls, value: object) -> TransactionStatus:
        return _safe_enum(value, cls, cls.COMPLETED)


class TransactionSource(StrEnum):
    MANUAL = "MANUAL"
    WHATSAPP = "WHATSAPP"
    TELEGRAM = "TELEGRAM"
    DASHBOARD = "DASHBOARD"
    IMPORT = "IMPORT"
    TRANSFER = "TRANSFER"

    @classmethod
    def safe(cls, value: object) -> TransactionSource:
        return _safe_enum(value, cls, cls.MANUAL)


# --- Transfer ---
class TransferStatus(StrEnum):
    ACTIVE = "ACTIVE"
    REVERSED = "REVERSED"

    @classmethod
    def safe(cls, value: object) -> TransferStatus:
        return _safe_enum(value, cls, cls.ACTIVE)


# --- Category ---
class CategoryStatus(StrEnum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"

    @classmethod
    def safe(cls, value: object) -> CategoryStatus:
        return _safe_enum(value, cls, cls.ACTIVE)


class CategoryType(StrEnum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"
    BOTH = "BOTH"

    @classmethod
    def safe(cls, value: object) -> CategoryType:
        return _safe_enum(value, cls, cls.BOTH)


# --- Loans / Debts ---
class InterestRateType(StrEnum):
    PERCENTAGE = "PERCENTAGE"
    FIXED_AMOUNT = "FIXED_AMOUNT"

    @classmethod
    def safe(cls, value: object) -> InterestRateType:
        return _safe_enum(value, cls, cls.PERCENTAGE)


class PaymentFrequency(StrEnum):
    WEEKLY = "WEEKLY"
    BIWEEKLY = "BIWEEKLY"
    MONTHLY = "MONTHLY"
    SINGLE = "SINGLE"

    @classmethod
    def safe(cls, value: object) -> PaymentFrequency:
        return _safe_enum(value, cls, cls.MONTHLY)


class AmortizationMethod(StrEnum):
    SIMPLE = "SIMPLE"
    FRENCH = "FRENCH"
    GERMAN = "GERMAN"

    @classmethod
    def safe(cls, value: object) -> AmortizationMethod:
        return _safe_enum(value, cls, cls.SIMPLE)


class LoanStatus(StrEnum):
    ACTIVE = "ACTIVE"
    PAID = "PAID"
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"

    @classmethod
    def safe(cls, value: object) -> LoanStatus:
        return _safe_enum(value, cls, cls.ACTIVE)


class InstallmentStatus(StrEnum):
    PENDING = "PENDING"
    PARTIAL = "PARTIAL"
    PAID = "PAID"
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"

    @classmethod
    def safe(cls, value: object) -> InstallmentStatus:
        return _safe_enum(value, cls, cls.PENDING)


# --- Budgets / Limits ---
class PeriodType(StrEnum):
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"

    @classmethod
    def safe(cls, value: object) -> PeriodType:
        return _safe_enum(value, cls, cls.MONTHLY)


class BudgetStatus(StrEnum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"

    @classmethod
    def safe(cls, value: object) -> BudgetStatus:
        return _safe_enum(value, cls, cls.ACTIVE)


# --- Notifications / Messages / Audit ---
class NotificationStatus(StrEnum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

    @classmethod
    def safe(cls, value: object) -> NotificationStatus:
        return _safe_enum(value, cls, cls.PENDING)


class Channel(StrEnum):
    WHATSAPP = "WHATSAPP"
    TELEGRAM = "TELEGRAM"
    DASHBOARD = "DASHBOARD"

    @classmethod
    def safe(cls, value: object) -> Channel:
        return _safe_enum(value, cls, cls.DASHBOARD)


class MessageDirection(StrEnum):
    INBOUND = "INBOUND"
    OUTBOUND = "OUTBOUND"

    @classmethod
    def safe(cls, value: object) -> MessageDirection:
        return _safe_enum(value, cls, cls.INBOUND)


class RecurrenceFrequency(StrEnum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    BIWEEKLY = "BIWEEKLY"
    MONTHLY = "MONTHLY"
    YEARLY = "YEARLY"

    @classmethod
    def safe(cls, value: object) -> RecurrenceFrequency:
        return _safe_enum(value, cls, cls.MONTHLY)
