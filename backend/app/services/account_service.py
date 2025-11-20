"""Service for account management and retrieval."""

from __future__ import annotations

from decimal import Decimal
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from app.models.enums import AccountStatus, AccountType, Currency
from app.schemas.account import AccountResponse, CurrencyTotal, UserBalanceResponse


class AccountService:
    """Provides helpers to manage user and system accounts."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_account(self, account_id: UUID) -> Optional[Account]:
        stmt = select(Account).where(Account.id == account_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_user_accounts(self, user_id: UUID) -> Sequence[Account]:
        stmt = (
            select(Account)
            .where(Account.user_id == user_id)
            .order_by(Account.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_or_create_user_account(
        self,
        user_id: UUID,
        currency: Currency,
        name: Optional[str] = None,
    ) -> Account:
        stmt = select(Account).where(
            Account.user_id == user_id,
            Account.currency == currency,
        )
        result = await self.session.execute(stmt)
        account = result.scalar_one_or_none()
        if account:
            return account

        account = Account(
            user_id=user_id,
            name=name or f"{currency.value.upper()} Wallet",
            currency=currency,
            type=AccountType.USER,
            status=AccountStatus.ACTIVE,
            balance=Decimal("0"),
            available_balance=Decimal("0"),
        )
        self.session.add(account)
        try:
            await self.session.flush()
        except IntegrityError as exc:  # pragma: no cover
            await self.session.rollback()
            raise ValueError("Unable to create account") from exc
        return account

    async def get_or_create_treasury_account(self, currency: Currency) -> Account:
        stmt = select(Account).where(
            Account.type == AccountType.TREASURY,
            Account.currency == currency,
        )
        result = await self.session.execute(stmt)
        account = result.scalar_one_or_none()
        if account:
            return account

        account = Account(
            user_id=None,
            name=f"Treasury {currency.value.upper()}",
            currency=currency,
            type=AccountType.TREASURY,
            status=AccountStatus.ACTIVE,
            balance=Decimal("0"),
            available_balance=Decimal("0"),
        )
        self.session.add(account)
        await self.session.flush()
        return account

    @staticmethod
    def to_schema(account: Account) -> AccountResponse:
        return AccountResponse.model_validate(account)

    async def get_user_balance_summary(self, user_id: UUID) -> UserBalanceResponse:
        accounts = await self.list_user_accounts(user_id)
        totals: dict[Currency, CurrencyTotal] = {}
        account_schemas = []
        for account in accounts:
            account_schema = AccountService.to_schema(account)
            account_schemas.append(account_schema)
            total = totals.get(account.currency)
            if not total:
                total = CurrencyTotal(
                    currency=account.currency,
                    balance=account.balance,
                    available_balance=account.available_balance,
                )
                totals[account.currency] = total
            else:
                total.balance += account.balance
                total.available_balance += account.available_balance

        return UserBalanceResponse(
            user_id=user_id,
            accounts=account_schemas,
            totals=list(totals.values()),
        )

    async def get_or_create_external_account(self, currency: Currency) -> Account:
        stmt = select(Account).where(
            Account.type == AccountType.EXTERNAL,
            Account.currency == currency,
        )
        result = await self.session.execute(stmt)
        account = result.scalar_one_or_none()
        if account:
            return account

        account = Account(
            user_id=None,
            name=f"External Settlement {currency.value.upper()}",
            currency=currency,
            type=AccountType.EXTERNAL,
            status=AccountStatus.ACTIVE,
            balance=Decimal("0"),
            available_balance=Decimal("0"),
        )
        self.session.add(account)
        await self.session.flush()
        return account
