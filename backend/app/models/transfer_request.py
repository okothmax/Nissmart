"""Transfer and withdrawal request models."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import GUID
from app.models.enums import Currency, RequestStatus
from app.models.mixins import TimestampMixin


class TransferRequest(Base, TimestampMixin):
    """Represents an internal transfer instruction between user accounts."""

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    request_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)

    source_account_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("account.id", ondelete="RESTRICT"), nullable=False
    )
    destination_account_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("account.id", ondelete="RESTRICT"), nullable=False
    )

    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[Currency] = mapped_column(nullable=False)

    status: Mapped[RequestStatus] = mapped_column(default=RequestStatus.PENDING, nullable=False)
    error_message: Mapped[str | None] = mapped_column(String(255), nullable=True)

    processed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("transaction.id", ondelete="SET NULL"), nullable=True
    )

    source_account: Mapped["Account"] = relationship(
        "Account", foreign_keys=[source_account_id], back_populates="outgoing_transfers"
    )
    destination_account: Mapped["Account"] = relationship(
        "Account", foreign_keys=[destination_account_id], back_populates="incoming_transfers"
    )
    transaction: Mapped[Optional["Transaction"]] = relationship("Transaction")


class WithdrawalRequest(Base, TimestampMixin):
    """Represents a simulated withdrawal to an external system."""

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    request_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)

    account_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("account.id", ondelete="RESTRICT"), nullable=False
    )

    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[Currency] = mapped_column(nullable=False)

    status: Mapped[RequestStatus] = mapped_column(default=RequestStatus.PENDING, nullable=False)
    external_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(255), nullable=True)

    processed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("transaction.id", ondelete="SET NULL"), nullable=True
    )

    account: Mapped["Account"] = relationship("Account", back_populates="withdrawal_requests")
    transaction: Mapped[Optional["Transaction"]] = relationship("Transaction")


if TYPE_CHECKING:  # pragma: no cover
    from app.models.account import Account
    from app.models.transaction import Transaction
