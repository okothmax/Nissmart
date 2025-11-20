"""Transaction query helpers."""

from __future__ import annotations

from datetime import date, datetime, time
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from app.models.enums import TransactionStatus, TransactionType
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionResponse


class TransactionService:
    """Provides read access to transactions."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_transactions(
        self,
        *,
        user_id: UUID | None = None,
        txn_type: TransactionType | None = None,
        status: TransactionStatus | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[Transaction]:
        stmt = select(Transaction).order_by(Transaction.created_at.desc())

        if user_id is not None:
            stmt = (
                stmt.join(Account, Account.id == Transaction.account_id)
                .where(
                    or_(
                        Transaction.user_id == user_id,
                        Account.user_id == user_id,
                    )
                )
            )

        if txn_type is not None:
            stmt = stmt.where(Transaction.type == txn_type)

        if status is not None:
            stmt = stmt.where(Transaction.status == status)

        if start_date is not None:
            stmt = stmt.where(Transaction.occurred_at >= datetime.combine(start_date, time.min))

        if end_date is not None:
            stmt = stmt.where(Transaction.occurred_at <= datetime.combine(end_date, time.max))

        stmt = stmt.offset(offset).limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def total_amount_by_type(self, txn_type: TransactionType) -> float:
        stmt = select(func.coalesce(func.sum(Transaction.amount), 0)).where(Transaction.type == txn_type)
        result = await self.session.execute(stmt)
        return float(result.scalar_one())

    async def count_transactions_by_type(
        self, txn_type: TransactionType
    ) -> int:
        stmt = select(func.count(Transaction.id)).where(Transaction.type == txn_type)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def total_wallet_value(self) -> float:
        stmt = select(func.coalesce(func.sum(Account.balance), 0))
        result = await self.session.execute(stmt)
        return float(result.scalar_one())

    async def count_transactions(
        self,
        *,
        user_id: UUID | None = None,
        txn_type: TransactionType | None = None,
        status: TransactionStatus | None = None,
    ) -> int:
        stmt = select(func.count(Transaction.id))

        if user_id is not None:
            stmt = (
                stmt.select_from(Transaction.__table__.join(Account.__table__, Account.id == Transaction.account_id))
                .where(
                    or_(
                        Transaction.user_id == user_id,
                        Account.user_id == user_id,
                    )
                )
            )
        else:
            stmt = stmt.select_from(Transaction)

        if txn_type is not None:
            stmt = stmt.where(Transaction.type == txn_type)

        if status is not None:
            stmt = stmt.where(Transaction.status == status)

        result = await self.session.execute(stmt)
        return result.scalar_one()

    @staticmethod
    def to_schema(transaction: Transaction) -> TransactionResponse:
        return TransactionResponse.model_validate(transaction)
