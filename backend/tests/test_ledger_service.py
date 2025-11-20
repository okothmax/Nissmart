"""Tests for LedgerService deposit, transfer, and withdrawal flows."""

from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy import select

from app.models.account import Account
from app.models.enums import Currency, LedgerEntryDirection, TransactionType
from app.models.transaction import LedgerEntry, Transaction
from app.models.user import User
from app.services.ledger_service import LedgerService


@pytest.mark.asyncio
async def test_deposit_creates_double_entry(session):
    user = User(email="alice@example.com", full_name="Alice Ledger")
    session.add(user)
    await session.flush()

    ledger_service = LedgerService(session)
    transaction = await ledger_service.deposit(
        user_id=user.id,
        amount=Decimal("150.00"),
        currency=Currency.KES,
        description="Initial funding",
    )

    assert transaction.type == TransactionType.DEPOSIT
    assert transaction.amount == Decimal("150.00")

    account = await session.get(Account, transaction.account_id)
    assert account.balance == Decimal("150.00")
    assert account.available_balance == Decimal("150.00")

    entries = (
        await session.execute(
            select(LedgerEntry).where(LedgerEntry.transaction_id == transaction.id)
        )
    ).scalars().all()
    assert len(entries) == 2
    directions = {entry.direction for entry in entries}
    assert directions == {LedgerEntryDirection.CREDIT, LedgerEntryDirection.DEBIT}


@pytest.mark.asyncio
async def test_transfer_moves_funds_between_accounts(session):
    user_a = User(email="bob@example.com", full_name="Bob Source")
    user_b = User(email="carol@example.com", full_name="Carol Destination")
    session.add_all([user_a, user_b])
    await session.flush()

    ledger_service = LedgerService(session)

    await ledger_service.deposit(
        user_id=user_a.id,
        amount=Decimal("200.00"),
        currency=Currency.KES,
    )
    await ledger_service.deposit(
        user_id=user_b.id,
        amount=Decimal("50.00"),
        currency=Currency.KES,
    )

    account_service = ledger_service.account_service
    source_account = await account_service.get_or_create_user_account(user_a.id, Currency.KES)
    destination_account = await account_service.get_or_create_user_account(
        user_b.id, Currency.KES
    )

    transfer_txn = await ledger_service.transfer(
        source_account_id=source_account.id,
        destination_account_id=destination_account.id,
        amount=Decimal("75.00"),
        currency=Currency.KES,
        description="Payment",
    )

    assert transfer_txn.type == TransactionType.TRANSFER

    refreshed_source = await session.get(Account, source_account.id)
    refreshed_destination = await session.get(Account, destination_account.id)
    assert refreshed_source.balance == Decimal("125.00")
    assert refreshed_destination.balance == Decimal("125.00")


@pytest.mark.asyncio
async def test_withdraw_reduces_balance(session):
    user = User(email="dave@example.com", full_name="Dave Withdraw")
    session.add(user)
    await session.flush()

    ledger_service = LedgerService(session)
    await ledger_service.deposit(
        user_id=user.id,
        amount=Decimal("120.00"),
        currency=Currency.KES,
    )

    withdrawal_txn = await ledger_service.withdraw(
        user_id=user.id,
        amount=Decimal("45.00"),
        currency=Currency.KES,
        description="Cash out",
    )

    assert withdrawal_txn.type == TransactionType.WITHDRAWAL

    account = await session.get(Account, withdrawal_txn.account_id)
    assert account.balance == Decimal("75.00")
    assert account.available_balance == Decimal("75.00")

    entries = (
        await session.execute(
            select(LedgerEntry).where(LedgerEntry.transaction_id == withdrawal_txn.id)
        )
    ).scalars().all()
    assert len(entries) == 2
    assert {entry.direction for entry in entries} == {
        LedgerEntryDirection.DEBIT,
        LedgerEntryDirection.CREDIT,
    }


@pytest.mark.asyncio
async def test_withdraw_raises_for_insufficient_balance(session):
    user = User(email="erin@example.com", full_name="Erin Limited")
    session.add(user)
    await session.flush()

    ledger_service = LedgerService(session)
    await ledger_service.deposit(
        user_id=user.id,
        amount=Decimal("10.00"),
        currency=Currency.KES,
    )

    with pytest.raises(ValueError, match="Insufficient available balance"):
        await ledger_service.withdraw(
            user_id=user.id,
            amount=Decimal("25.00"),
            currency=Currency.KES,
        )
