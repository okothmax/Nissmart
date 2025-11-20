"""Account (wallet) model."""

from __future__ import annotations

from decimal import Decimal
import uuid

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import TYPE_CHECKING, Optional

from app.db.base import Base
from app.db.types import GUID
from app.models.enums import AccountStatus, AccountType, Currency
from app.models.mixins import TimestampMixin


class Account(Base, TimestampMixin):
    """Represents a wallet/account holding user funds."""

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    currency: Mapped[Currency] = mapped_column(default=Currency.KES, nullable=False)
    type: Mapped[AccountType] = mapped_column(default=AccountType.USER, nullable=False)
    status: Mapped[AccountStatus] = mapped_column(default=AccountStatus.ACTIVE, nullable=False)

    balance: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0"))
    available_balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0"), doc="Balance available for withdrawal"
    )

    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    ledger_entries: Mapped[list["LedgerEntry"]] = relationship(
        "LedgerEntry", back_populates="account", cascade="all, delete-orphan"
    )
    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction", back_populates="account", cascade="all"
    )
    user: Mapped[Optional["User"]] = relationship("User", back_populates="accounts")
    outgoing_transfers: Mapped[list["TransferRequest"]] = relationship(
        "TransferRequest",
        back_populates="source_account",
        cascade="all, delete-orphan",
        foreign_keys="TransferRequest.source_account_id",
    )
    incoming_transfers: Mapped[list["TransferRequest"]] = relationship(
        "TransferRequest",
        back_populates="destination_account",
        cascade="all, delete-orphan",
        foreign_keys="TransferRequest.destination_account_id",
    )
    withdrawal_requests: Mapped[list["WithdrawalRequest"]] = relationship(
        "WithdrawalRequest",
        back_populates="account",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("user_id", "currency", name="uq_user_currency"),
        CheckConstraint("balance >= 0", name="ck_balance_non_negative"),
        CheckConstraint(
            "available_balance >= 0", name="ck_available_balance_non_negative"
        ),
        CheckConstraint(
            "available_balance <= balance", name="ck_available_leq_balance"
        ),
    )

    __mapper_args__ = {"version_id_col": version}


if TYPE_CHECKING:  # pragma: no cover
    from app.models.ledger_entry import LedgerEntry
    from app.models.transaction import Transaction
    from app.models.transfer_request import TransferRequest, WithdrawalRequest
    from app.models.user import User
