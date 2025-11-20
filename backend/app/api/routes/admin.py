"""Admin dashboard routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.dashboard import AdminSummaryResponse
from app.services.transaction_service import TransactionService
from app.models.enums import TransactionType
from app.services.user_service import UserService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/admin", response_model=AdminSummaryResponse)
async def get_admin_summary(
    session: AsyncSession = Depends(get_db),
) -> AdminSummaryResponse:
    user_service = UserService(session)
    transaction_service = TransactionService(session)

    total_users = await user_service.count_users()
    total_wallet_value = await transaction_service.total_wallet_value()
    total_deposits = await transaction_service.count_transactions_by_type(TransactionType.DEPOSIT)
    total_transfers = await transaction_service.count_transactions_by_type(TransactionType.TRANSFER)
    total_withdrawals = await transaction_service.count_transactions_by_type(TransactionType.WITHDRAWAL)
    total_deposits_amount = await transaction_service.total_amount_by_type(TransactionType.DEPOSIT)
    total_transfers_amount = await transaction_service.total_amount_by_type(TransactionType.TRANSFER)
    total_withdrawals_amount = await transaction_service.total_amount_by_type(TransactionType.WITHDRAWAL)

    return AdminSummaryResponse(
        total_users=total_users,
        total_wallet_value=total_wallet_value,
        total_deposits=total_deposits,
        total_transfers=total_transfers,
        total_withdrawals=total_withdrawals,
        total_deposits_amount=total_deposits_amount,
        total_transfers_amount=total_transfers_amount,
        total_withdrawals_amount=total_withdrawals_amount,
    )
