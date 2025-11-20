"""Pydantic schemas for account resources."""

from __future__ import annotations

from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import Field

from app.models.enums import AccountStatus, AccountType, Currency
from app.schemas.base import APIModel, TimestampedModel


class AccountResponse(TimestampedModel):
    user_id: Optional[UUID]
    name: str
    currency: Currency
    type: AccountType
    status: AccountStatus
    balance: Decimal = Field(decimal_places=2)
    available_balance: Decimal = Field(decimal_places=2)


class BalanceResponse(TimestampedModel):
    account_id: UUID
    balance: Decimal = Field(decimal_places=2)
    available_balance: Decimal = Field(decimal_places=2)
    currency: Currency


class CurrencyTotal(APIModel):
    currency: Currency
    balance: Decimal = Field(decimal_places=2)
    available_balance: Decimal = Field(decimal_places=2)


class UserBalanceResponse(APIModel):
    user_id: UUID
    accounts: list[AccountResponse]
    totals: list[CurrencyTotal]
