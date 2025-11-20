"""Transaction and ledger entry models."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import TYPE_CHECKING, Optional

from app.db.base import Base
from app.db.types import GUID
from app.models.enums import Currency, LedgerEntryDirection, TransactionStatus, TransactionType
from app.models.mixins import TimestampMixin


class Transaction(Base, TimestampMixin):
    """Financial transaction recorded in the ledger."""

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    reference: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)

    user_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("user.id"), nullable=True)
    account_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("account.id"), nullable=False)

    type: Mapped[TransactionType] = mapped_column(nullable=False)
    status: Mapped[TransactionStatus] = mapped_column(default=TransactionStatus.PENDING, nullable=False)

    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[Currency] = mapped_column(nullable=False, default=Currency.KES)

    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    context_data: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    user: Mapped[Optional["User"]] = relationship("User", back_populates="transactions")
    account: Mapped["Account"] = relationship("Account", back_populates="transactions")
    ledger_entries: Mapped[list["LedgerEntry"]] = relationship(
        "LedgerEntry", back_populates="transaction", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("reference", name="uq_transaction_reference"),
        Index("ix_transaction_user_account", "user_id", "account_id"),
    )


class LedgerEntry(Base, TimestampMixin):
    """Double-entry bookkeeping record tied to a transaction."""

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)

    transaction_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("transaction.id", ondelete="CASCADE"), nullable=False
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("account.id", ondelete="CASCADE"), nullable=False
    )

    direction: Mapped[LedgerEntryDirection] = mapped_column(nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    balance_after: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    available_balance_after: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    note: Mapped[str | None] = mapped_column(String(255), nullable=True)

    account: Mapped["Account"] = relationship("Account", back_populates="ledger_entries")
    transaction: Mapped["Transaction"] = relationship("Transaction", back_populates="ledger_entries")


if TYPE_CHECKING:  # pragma: no cover
    from app.models.account import Account
    from app.models.user import User
