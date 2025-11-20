"""Schemas for transaction operations."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import Currency, TransactionStatus, TransactionType
from app.schemas.base import APIModel, TimestampedModel


class TransactionResponse(TimestampedModel):
    reference: str
    user_id: Optional[UUID]
    account_id: UUID
    type: TransactionType
    status: TransactionStatus
    amount: Decimal = Field(decimal_places=2)
    currency: Currency
    description: Optional[str]
    occurred_at: datetime
    context_data: dict | None = None


class DepositRequest(BaseModel):
    user_id: UUID
    amount: Decimal = Field(decimal_places=2, gt=0)
    currency: Currency
    description: Optional[str] = None
    reference: Optional[str] = None


class TransferRequest(BaseModel):
    source_user_id: UUID
    destination_user_id: UUID
    amount: Decimal = Field(decimal_places=2, gt=0)
    currency: Currency
    description: Optional[str] = None
    reference: Optional[str] = None


class WithdrawalRequest(BaseModel):
    user_id: UUID
    amount: Decimal = Field(decimal_places=2, gt=0)
    currency: Currency
    description: Optional[str] = None
    reference: Optional[str] = None


class TransactionListResponse(APIModel):
    items: list[TransactionResponse]
    total: int
