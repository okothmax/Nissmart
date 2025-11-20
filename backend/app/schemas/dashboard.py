"""Schemas for admin/dashboard responses."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AdminSummaryResponse(BaseModel):
    total_users: int = Field(..., ge=0)
    total_wallet_value: float = Field(..., ge=0)
    total_deposits: int = Field(..., ge=0)
    total_transfers: int = Field(..., ge=0)
    total_withdrawals: int = Field(..., ge=0)
    total_deposits_amount: float = Field(..., ge=0)
    total_transfers_amount: float = Field(..., ge=0)
    total_withdrawals_amount: float = Field(..., ge=0)
