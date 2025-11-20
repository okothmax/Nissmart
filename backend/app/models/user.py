"""User model."""

from __future__ import annotations

import uuid

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import TYPE_CHECKING

from app.db.base import Base
from app.db.types import GUID
from app.models.mixins import TimestampMixin


class User(Base, TimestampMixin):
    """Represents an end user in the Nissmart ecosystem."""

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    accounts: Mapped[list["Account"]] = relationship(
        "Account",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction",
        back_populates="user",
        cascade="all",
    )


if TYPE_CHECKING:  # pragma: no cover
    from app.models.account import Account
    from app.models.transaction import Transaction
