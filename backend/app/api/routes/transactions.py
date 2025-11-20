"""Transaction-related API routes."""

from __future__ import annotations

from typing import Sequence
from uuid import UUID

from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.enums import TransactionStatus, TransactionType
from app.schemas.transaction import TransactionListResponse
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("", response_model=TransactionListResponse)
async def list_transactions(
    user_id: UUID | None = Query(default=None),
    txn_type: TransactionType | None = Query(default=None, alias="type"),
    status: TransactionStatus | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db),
) -> TransactionListResponse:
    service = TransactionService(session)

    transactions: Sequence = await service.list_transactions(
        user_id=user_id,
        txn_type=txn_type,
        status=status,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )

    total = await service.count_transactions(
        user_id=user_id,
        txn_type=txn_type,
        status=status,
    )

    items = [TransactionService.to_schema(txn) for txn in transactions]
    return TransactionListResponse(items=items, total=total)
