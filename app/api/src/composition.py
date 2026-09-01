from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from modules.users.application.use_cases.create_user import CreateUserUseCase
from modules.users.infrastructure.adapters.sqlalchemy_user_repository import SqlAlchemyUserRepository

from modules.accounts.application.use_cases.create_account import CreateAccountUseCase
from modules.accounts.infrastructure.repositories.sqlalchemy_account_repository import SqlAlchemyAccountRepository

from modules.transactions.application.use_cases.create_transaction import CreateTransactionUseCase
from modules.transactions.infrastructure.adapters.sqlalchemy_transaction_repository import SqlAlchemyTransactionRepository


def build_create_user_use_case(session: AsyncSession) -> CreateUserUseCase:
    repo = SqlAlchemyUserRepository(session)
    return CreateUserUseCase(repo)


def build_user_repository(session: AsyncSession) -> SqlAlchemyUserRepository:
    return SqlAlchemyUserRepository(session)


def build_create_account_use_case(session: AsyncSession) -> CreateAccountUseCase:
    repo = SqlAlchemyAccountRepository(session)
    return CreateAccountUseCase(repo)


def build_account_repository(session: AsyncSession) -> SqlAlchemyAccountRepository:
    return SqlAlchemyAccountRepository(session)


def build_create_transaction_use_case(session: AsyncSession) -> CreateTransactionUseCase:
    repo = SqlAlchemyTransactionRepository(session)
    return CreateTransactionUseCase(repo)


def build_transaction_repository(session: AsyncSession) -> SqlAlchemyTransactionRepository:
    return SqlAlchemyTransactionRepository(session)
