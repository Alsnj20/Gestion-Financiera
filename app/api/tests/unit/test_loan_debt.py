"""Unit tests for Loan/Debt entities + use cases (fakes, no DB)."""

from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi import HTTPException

from modules.debts.application.use_cases.cancel_debt import (
    CancelDebtInput,
    CancelDebtUseCase,
)
from modules.debts.application.use_cases.create_debt import (
    CreateDebtInput,
    CreateDebtUseCase,
)
from modules.debts.domain.entities.debt import Debt, DebtInstallment
from modules.debts.presentation.controllers.debt_controller import DebtController
from modules.loans.application.use_cases.cancel_loan import (
    CancelLoanInput,
    CancelLoanUseCase,
)
from modules.loans.application.use_cases.create_loan import (
    CreateLoanInput,
    CreateLoanUseCase,
)
from modules.loans.domain.entities.loan import Loan, LoanInstallment
from modules.loans.presentation.controllers.loan_controller import LoanController
from shared.errors import BusinessRuleError, ValidationError
from shared.types.enums import InstallmentStatus, LoanStatus


class FakeLoanRepo:
    def __init__(self, loans: list[Loan] | None = None) -> None:
        self.store: dict[str, Loan] = {a.id: a for a in (loans or [])}
        self.schedules: dict[str, list] = {}
        self.payments: dict[str, list] = {}

    async def save(self, loan: Loan) -> None:
        self.store[loan.id] = loan

    async def find_by_id(
        self, loan_id: str, *, for_update: bool = False
    ) -> Loan | None:
        return self.store.get(loan_id)

    async def find_by_user(self, user_id: str) -> list[Loan]:
        return [a for a in self.store.values() if a.user_id == user_id]

    async def save_installments(self, installments: list) -> None:
        for inst in installments:
            self.schedules.setdefault(inst.loan_id, []).append(inst)

    async def list_installments(self, loan_id: str) -> list:
        return sorted(
            self.schedules.get(loan_id, []), key=lambda i: i.installment_number
        )

    async def save_installment(self, installment) -> None:
        sched = self.schedules.setdefault(installment.loan_id, [])
        sched[:] = [i for i in sched if i.id != installment.id] + [installment]

    async def save_payment(self, payment) -> None:
        self.payments.setdefault(payment.loan_id, []).append(payment)

    async def list_payments(self, loan_id: str) -> list:
        return self.payments.get(loan_id, [])


class FakeDebtRepo:
    def __init__(self, debts: list[Debt] | None = None) -> None:
        self.store: dict[str, Debt] = {a.id: a for a in (debts or [])}
        self.schedules: dict[str, list] = {}
        self.payments: dict[str, list] = {}

    async def save(self, debt: Debt) -> None:
        self.store[debt.id] = debt

    async def find_by_id(
        self, debt_id: str, *, for_update: bool = False
    ) -> Debt | None:
        return self.store.get(debt_id)

    async def find_by_user(self, user_id: str) -> list[Debt]:
        return [a for a in self.store.values() if a.user_id == user_id]

    async def save_installments(self, installments: list) -> None:
        for inst in installments:
            self.schedules.setdefault(inst.debt_id, []).append(inst)

    async def list_installments(self, debt_id: str) -> list:
        return sorted(
            self.schedules.get(debt_id, []), key=lambda i: i.installment_number
        )

    async def save_installment(self, installment) -> None:
        sched = self.schedules.setdefault(installment.debt_id, [])
        sched[:] = [i for i in sched if i.id != installment.id] + [installment]

    async def save_payment(self, payment) -> None:
        self.payments.setdefault(payment.debt_id, []).append(payment)

    async def list_payments(self, debt_id: str) -> list:
        return self.payments.get(debt_id, [])


class FakeSession:
    async def commit(self) -> None:
        pass

    async def rollback(self) -> None:
        pass


class FakeTxRepo:
    def __init__(self) -> None:
        self.store: dict = {}

    async def save(self, tx) -> None:
        self.store[tx.id] = tx

    async def find_by_id(self, tx_id: str, **kwargs):
        return self.store.get(tx_id)

    async def list_by_user(self, user_id: str, **kwargs):
        return [t for t in self.store.values() if t.user_id == user_id]


class FakeAccRepo:
    def __init__(self, accounts=None) -> None:
        self.store: dict = {a.id: a for a in (accounts or [])}

    async def save(self, account) -> None:
        self.store[account.id] = account

    async def find_by_id(self, account_id: str, **kwargs):
        return self.store.get(account_id)


def _loan_controller(repo):

    return LoanController(repo, FakeTxRepo(), FakeAccRepo(), FakeSession())


def _debt_controller(repo):

    return DebtController(repo, FakeTxRepo(), FakeAccRepo(), FakeSession())


def _loan(**kwargs) -> Loan:

    base = {
        "user_id": "user-1",
        "borrower_name": "Pedro",
        "principal_amount": Decimal("1000.00"),
    }
    base.update(kwargs)
    return Loan.create(**base)


def _debt(**kwargs) -> Debt:
    base = {
        "user_id": "user-1",
        "creditor_name": "Banco",
        "principal_amount": Decimal("500.00"),
    }
    base.update(kwargs)
    return Debt.create(**base)


def test_loan_negative_rate_rejected():
    """Money traga negativos: el guard crudo debe rechazarlos."""
    with pytest.raises(ValidationError) as exc:
        _loan(interest_rate=Decimal("-5.00"))
    assert exc.value.code == "LOAN_RATE_NEGATIVE"


def test_debt_negative_rate_rejected():
    """Debt no tenía este check (asimetría vs loans)."""
    with pytest.raises(ValidationError) as exc:
        _debt(interest_rate=Decimal("-5.00"))
    assert exc.value.code == "DEBT_RATE_NEGATIVE"


def test_debt_installment_parity_with_loan():
    """DebtInstallment recupera la paridad: apply/mark/is_paid."""
    from datetime import date

    for cls, fk in ((LoanInstallment, "loan_id"), (DebtInstallment, "debt_id")):
        inst = cls(
            id="i-1",
            **{fk: "x-1"},
            installment_number=1,
            due_date=date(2020, 1, 1),
            principal_due=Decimal("100.00"),
            interest_due=Decimal("10.00"),
            total_due=Decimal("110.00"),
        )
        assert inst.is_paid is False
        paid = inst.apply_payment(Decimal("100.00"), Decimal("10.00"))
        assert paid.is_paid is True
        overdue = inst.mark_overdue_if_needed(ref_date=date(2020, 6, 1))
        assert overdue.status == InstallmentStatus.OVERDUE


async def test_loan_cancel_keeps_row():
    repo = FakeLoanRepo([_loan()])
    loan = next(iter(repo.store.values()))
    out = await CancelLoanUseCase(repo).execute(
        CancelLoanInput(loan_id=loan.id, requester_id="user-1")
    )
    assert out.status == "CANCELLED"
    assert repo.store[loan.id].status == LoanStatus.CANCELLED


async def test_loan_cancel_sweeps_pending_installments():
    from modules.loans.application.use_cases.create_loan import (
        CreateLoanInput,
        CreateLoanUseCase,
    )
    from modules.loans.application.use_cases.get_loan import (
        GetLoanInput,
        GetLoanUseCase,
    )

    repo = FakeLoanRepo()
    out = await CreateLoanUseCase(repo).execute(
        CreateLoanInput(
            user_id="user-1",
            borrower_name="Pedro",
            principal_amount=Decimal("300.00"),
            installment_count=3,
        )
    )
    # Marco la primera como pagada a mano (simula un pago parcial previo).
    sched = repo.schedules[out.id]
    sched[0] = sched[0]._with(status=InstallmentStatus.PAID)

    await CancelLoanUseCase(repo).execute(
        CancelLoanInput(loan_id=out.id, requester_id="user-1")
    )
    got = await GetLoanUseCase(repo).execute(
        GetLoanInput(loan_id=out.id, requester_id="user-1")
    )
    statuses = [i.status for i in got.installments]
    assert statuses[0] == "PAID"  # lo pagado se respeta
    assert statuses[1:] == ["CANCELLED", "CANCELLED"]  # barrido
    assert got.status == "CANCELLED"


async def test_loan_cancel_forbidden_for_other():
    repo = FakeLoanRepo([_loan()])
    loan = next(iter(repo.store.values()))
    with pytest.raises(BusinessRuleError) as exc:
        await CancelLoanUseCase(repo).execute(
            CancelLoanInput(loan_id=loan.id, requester_id="other")
        )
    assert exc.value.code == "FORBIDDEN"


async def test_loan_cancel_paid_rejected():
    repo = FakeLoanRepo([_loan()])
    loan = next(iter(repo.store.values()))
    repo.store[loan.id] = loan._with(status=LoanStatus.PAID)
    with pytest.raises(BusinessRuleError) as exc:
        await CancelLoanUseCase(repo).execute(
            CancelLoanInput(loan_id=loan.id, requester_id="user-1")
        )
    assert exc.value.code == "LOAN_ALREADY_PAID"


async def test_debt_create_and_cancel_flow():
    repo = FakeDebtRepo()
    out = await CreateDebtUseCase(repo).execute(
        CreateDebtInput(
            user_id="user-1", creditor_name="Banco", principal_amount=Decimal("500.00")
        )
    )
    assert out.status == "ACTIVE"
    assert len(out.installments) == 1  # contado por defecto
    assert out.installments[0].total_due == Decimal("500.00")
    cancelled = await CancelDebtUseCase(repo).execute(
        CancelDebtInput(debt_id=out.id, requester_id="user-1")
    )
    assert cancelled.status == "CANCELLED"
    # Sin borrado físico: la fila sigue.
    assert out.id in repo.store


async def test_loan_schedule_monthly_with_interest():
    from datetime import date

    from modules.loans.application.use_cases.get_loan import (
        GetLoanInput,
        GetLoanUseCase,
    )

    repo = FakeLoanRepo()
    controller = _loan_controller(repo)
    out = await controller.create(
        CreateLoanInput(
            user_id="user-1",
            borrower_name="Pedro",
            principal_amount=Decimal("1200.00"),
            interest_rate=Decimal("10.00"),
            installment_count=12,
            first_due_date=date(2026, 1, 15),
        )
    )
    assert len(out["installments"]) == 12
    totals = [i["total_due"] for i in out["installments"]]
    assert sum(totals, Decimal("0.00")) == Decimal("1320.00")  # 1200 + 10%
    assert out["installments"][0]["due_date"] == date(2026, 1, 15)
    assert out["installments"][-1]["due_date"] == date(2026, 12, 15)
    got = await GetLoanUseCase(repo).execute(
        GetLoanInput(loan_id=out["id"], requester_id="user-1")
    )
    assert len(got.installments) == 12  # get expone el cronograma


async def test_loan_controller_create_and_cancel():
    repo = FakeLoanRepo()
    controller = _loan_controller(repo)
    out = await controller.create(
        CreateLoanInput(
            user_id="user-1", borrower_name="Pedro", principal_amount=Decimal("1000.00")
        )
    )
    assert out["status"] == "ACTIVE"
    cancelled = await controller.cancel(
        CancelLoanInput(loan_id=out["id"], requester_id="user-1")
    )
    assert cancelled["status"] == "CANCELLED"


async def test_debt_controller_forbidden_maps_403():
    repo = FakeDebtRepo([_debt()])
    debt = next(iter(repo.store.values()))
    controller = _debt_controller(repo)
    with pytest.raises(HTTPException) as exc:
        await controller.cancel(CancelDebtInput(debt_id=debt.id, requester_id="other"))
    assert exc.value.status_code == 403


# ---------- register payments ----------


def _account_with(balance: str):
    from modules.accounts.domain.entities.account import Account

    return Account.create(
        user_id="user-1", name="Caja", initial_balance=Decimal(balance)
    )


async def test_loan_full_payment_closes_loan():
    from modules.loans.application.use_cases.create_loan import CreateLoanInput
    from modules.loans.application.use_cases.register_loan_payment import (
        RegisterLoanPaymentInput,
        RegisterLoanPaymentUseCase,
    )

    loan_repo, tx_repo, acc_repo = (
        FakeLoanRepo(),
        FakeTxRepo(),
        FakeAccRepo([_account_with("1000.00")]),
    )
    account = next(iter(acc_repo.store.values()))
    out = await CreateLoanUseCase(loan_repo).execute(
        CreateLoanInput(
            user_id="user-1", borrower_name="Pedro", principal_amount=Decimal("300.00")
        )
    )
    sched = loan_repo.schedules[out.id]
    assert len(sched) == 1  # contado

    paid = await RegisterLoanPaymentUseCase(loan_repo, tx_repo, acc_repo).execute(
        RegisterLoanPaymentInput(
            loan_id=out.id,
            requester_id="user-1",
            account_id=account.id,
            installment_id=sched[0].id,
            principal_amount=Decimal("300.00"),
        )
    )
    assert paid.installment_status == "PAID"
    assert paid.loan_status == "PAID"  # última cuota cierra el préstamo
    assert acc_repo.store[account.id].current_balance == Decimal("1300.00")  # INCOME
    tx = tx_repo.store[paid.transaction_id]
    assert tx.type.value == "INCOME"


async def test_loan_partial_payment_keeps_open():
    from modules.loans.application.use_cases.create_loan import CreateLoanInput
    from modules.loans.application.use_cases.register_loan_payment import (
        RegisterLoanPaymentInput,
        RegisterLoanPaymentUseCase,
    )

    loan_repo, tx_repo, acc_repo = (
        FakeLoanRepo(),
        FakeTxRepo(),
        FakeAccRepo([_account_with("0.00")]),
    )
    account = next(iter(acc_repo.store.values()))
    out = await CreateLoanUseCase(loan_repo).execute(
        CreateLoanInput(
            user_id="user-1",
            borrower_name="Pedro",
            principal_amount=Decimal("300.00"),
            installment_count=3,
        )
    )
    first = loan_repo.schedules[out.id][0]
    paid = await RegisterLoanPaymentUseCase(loan_repo, tx_repo, acc_repo).execute(
        RegisterLoanPaymentInput(
            loan_id=out.id,
            requester_id="user-1",
            account_id=account.id,
            installment_id=first.id,
            principal_amount=Decimal("40.00"),
        )
    )
    assert paid.installment_status == "PARTIAL"
    assert paid.loan_status == "ACTIVE"  # quedan cuotas pendientes


async def test_loan_overpay_rejected():
    from modules.loans.application.use_cases.create_loan import CreateLoanInput
    from modules.loans.application.use_cases.register_loan_payment import (
        RegisterLoanPaymentInput,
        RegisterLoanPaymentUseCase,
    )

    loan_repo, tx_repo, acc_repo = (
        FakeLoanRepo(),
        FakeTxRepo(),
        FakeAccRepo([_account_with("0.00")]),
    )
    account = next(iter(acc_repo.store.values()))
    out = await CreateLoanUseCase(loan_repo).execute(
        CreateLoanInput(
            user_id="user-1", borrower_name="Pedro", principal_amount=Decimal("100.00")
        )
    )
    sched = loan_repo.schedules[out.id]
    with pytest.raises(ValidationError) as exc:
        await RegisterLoanPaymentUseCase(loan_repo, tx_repo, acc_repo).execute(
            RegisterLoanPaymentInput(
                loan_id=out.id,
                requester_id="user-1",
                account_id=account.id,
                installment_id=sched[0].id,
                principal_amount=Decimal("150.00"),
            )
        )
    assert exc.value.code == "LOAN_PAYMENT_EXCEEDS"
    assert acc_repo.store[account.id].current_balance == Decimal("0.00")  # intacto


async def test_debt_payment_is_expense():
    from modules.debts.application.use_cases.create_debt import CreateDebtInput
    from modules.debts.application.use_cases.register_debt_payment import (
        RegisterDebtPaymentInput,
        RegisterDebtPaymentUseCase,
    )

    debt_repo, tx_repo, acc_repo = (
        FakeDebtRepo(),
        FakeTxRepo(),
        FakeAccRepo([_account_with("1000.00")]),
    )
    account = next(iter(acc_repo.store.values()))
    out = await CreateDebtUseCase(debt_repo).execute(
        CreateDebtInput(
            user_id="user-1", creditor_name="Banco", principal_amount=Decimal("200.00")
        )
    )
    sched = debt_repo.schedules[out.id]
    paid = await RegisterDebtPaymentUseCase(debt_repo, tx_repo, acc_repo).execute(
        RegisterDebtPaymentInput(
            debt_id=out.id,
            requester_id="user-1",
            account_id=account.id,
            installment_id=sched[0].id,
            principal_amount=Decimal("200.00"),
        )
    )
    assert paid.debt_status == "PAID"
    assert acc_repo.store[account.id].current_balance == Decimal("800.00")  # EXPENSE
    tx = tx_repo.store[paid.transaction_id]
    assert tx.type.value == "EXPENSE"
