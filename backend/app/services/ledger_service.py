"""Ledger and transaction operations ensuring double-entry safety."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models.account import Account
from app.models.enums import (
    Currency,
    LedgerEntryDirection,
    TransactionStatus,
    TransactionType,
)
from app.models.transaction import LedgerEntry, Transaction
from app.services.account_service import AccountService


class LedgerService:
    """Handles deposits, transfers, and withdrawals with double-entry bookkeeping."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.account_service = AccountService(session)

    async def _lock_account(self, account_id: UUID) -> Account:
        stmt = select(Account).where(Account.id == account_id).with_for_update()
        result = await self.session.execute(stmt)
        account = result.scalar_one_or_none()
        if not account:
            raise ValueError("Account not found")
        return account

    async def _create_transaction(
        self,
        *,
        user_id: Optional[UUID],
        account: Account,
        txn_type: TransactionType,
        amount: Decimal,
        currency: Currency,
        description: Optional[str] = None,
        metadata: Optional[dict] = None,
        reference: Optional[str] = None,
    ) -> Transaction:
        transaction = Transaction(
            id=uuid4(),
            reference=reference or uuid4().hex,
            user_id=user_id,
            account_id=account.id,
            type=txn_type,
            status=TransactionStatus.COMPLETED,
            amount=amount,
            currency=currency,
            description=description,
            context_data=metadata or {},
            occurred_at=datetime.now(timezone.utc),
        )
        self.session.add(transaction)
        await self.session.flush()
        return transaction

    async def _create_ledger_entry(
        self,
        *,
        transaction: Transaction,
        account: Account,
        direction: LedgerEntryDirection,
        amount: Decimal,
        balance_after: Decimal,
        available_after: Decimal,
        note: Optional[str] = None,
    ) -> LedgerEntry:
        entry = LedgerEntry(
            transaction_id=transaction.id,
            account_id=account.id,
            direction=direction,
            amount=amount,
            balance_after=balance_after,
            available_balance_after=available_after,
            note=note,
        )
        self.session.add(entry)
        return entry

    async def deposit(
        self,
        *,
        user_id: UUID,
        amount: Decimal,
        currency: Currency,
        description: Optional[str] = None,
        reference: Optional[str] = None,
    ) -> Transaction:
        if amount <= Decimal("0"):
            raise ValueError("Deposit amount must be positive")

        user_account = await self.account_service.get_or_create_user_account(
            user_id=user_id,
            currency=currency,
        )
        treasury_account = await self.account_service.get_or_create_treasury_account(currency)

        locked_user_account = await self._lock_account(user_account.id)
        locked_treasury_account = await self._lock_account(treasury_account.id)

        locked_user_account.balance += amount
        locked_user_account.available_balance += amount

        locked_treasury_account.balance += amount
        locked_treasury_account.available_balance += amount

        transaction = await self._create_transaction(
            user_id=user_id,
            account=locked_user_account,
            txn_type=TransactionType.DEPOSIT,
            amount=amount,
            currency=currency,
            description=description,
            metadata={"treasury_account_id": str(locked_treasury_account.id)},
            reference=reference,
        )

        await self._create_ledger_entry(
            transaction=transaction,
            account=locked_user_account,
            direction=LedgerEntryDirection.CREDIT,
            amount=amount,
            balance_after=locked_user_account.balance,
            available_after=locked_user_account.available_balance,
            note="Deposit credit",
        )

        await self._create_ledger_entry(
            transaction=transaction,
            account=locked_treasury_account,
            direction=LedgerEntryDirection.DEBIT,
            amount=amount,
            balance_after=locked_treasury_account.balance,
            available_after=locked_treasury_account.available_balance,
            note="Deposit offset",
        )

        return transaction

    async def transfer(
        self,
        *,
        source_account_id: UUID,
        destination_account_id: UUID,
        amount: Decimal,
        currency: Currency,
        description: Optional[str] = None,
        reference: Optional[str] = None,
    ) -> Transaction:
        if source_account_id == destination_account_id:
            raise ValueError("Cannot transfer to the same account")
        if amount <= Decimal("0"):
            raise ValueError("Transfer amount must be positive")

        source_account = await self._lock_account(source_account_id)
        destination_account = await self._lock_account(destination_account_id)

        if source_account.currency != currency or destination_account.currency != currency:
            raise ValueError("Currency mismatch between accounts")
        if source_account.available_balance < amount:
            raise ValueError("Insufficient available balance")

        source_account.balance -= amount
        source_account.available_balance -= amount

        destination_account.balance += amount
        destination_account.available_balance += amount

        transaction = await self._create_transaction(
            user_id=source_account.user_id,
            account=source_account,
            txn_type=TransactionType.TRANSFER,
            amount=amount,
            currency=currency,
            description=description,
            metadata={"destination_account_id": str(destination_account_id)},
            reference=reference,
        )

        await self._create_ledger_entry(
            transaction=transaction,
            account=source_account,
            direction=LedgerEntryDirection.DEBIT,
            amount=amount,
            balance_after=source_account.balance,
            available_after=source_account.available_balance,
            note="Transfer debit",
        )
        await self._create_ledger_entry(
            transaction=transaction,
            account=destination_account,
            direction=LedgerEntryDirection.CREDIT,
            amount=amount,
            balance_after=destination_account.balance,
            available_after=destination_account.available_balance,
            note="Transfer credit",
        )

        return transaction

    async def withdraw(
        self,
        *,
        user_id: UUID,
        amount: Decimal,
        currency: Currency,
        description: Optional[str] = None,
        reference: Optional[str] = None,
    ) -> Transaction:
        if amount <= Decimal("0"):
            raise ValueError("Withdrawal amount must be positive")

        user_account = await self.account_service.get_or_create_user_account(
            user_id=user_id,
            currency=currency,
        )
        external_account = await self.account_service.get_or_create_external_account(currency)

        locked_user_account = await self._lock_account(user_account.id)
        locked_external_account = await self._lock_account(external_account.id)

        if locked_user_account.available_balance < amount:
            raise ValueError("Insufficient available balance")

        locked_user_account.balance -= amount
        locked_user_account.available_balance -= amount

        locked_external_account.balance += amount
        locked_external_account.available_balance += amount

        transaction = await self._create_transaction(
            user_id=user_id,
            account=locked_user_account,
            txn_type=TransactionType.WITHDRAWAL,
            amount=amount,
            currency=currency,
            description=description,
            metadata={"external_account_id": str(locked_external_account.id)},
            reference=reference,
        )

        await self._create_ledger_entry(
            transaction=transaction,
            account=locked_user_account,
            direction=LedgerEntryDirection.DEBIT,
            amount=amount,
            balance_after=locked_user_account.balance,
            available_after=locked_user_account.available_balance,
            note="Withdrawal debit",
        )
        await self._create_ledger_entry(
            transaction=transaction,
            account=locked_external_account,
            direction=LedgerEntryDirection.CREDIT,
            amount=amount,
            balance_after=locked_external_account.balance,
            available_after=locked_external_account.available_balance,
            note="Withdrawal offset",
        )

        return transaction
