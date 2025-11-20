"""Ledger operation endpoints (deposit, transfer, withdraw, balances)."""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_idempotency_service
from app.schemas.account import UserBalanceResponse
from app.schemas.transaction import (
    DepositRequest,
    TransactionResponse,
    TransferRequest,
    WithdrawalRequest,
)
from app.services.account_service import AccountService
from app.services.idempotency import IdempotencyService
from app.services.ledger_service import LedgerService
from app.services.transaction_service import TransactionService
from app.utils.hash_utils import hash_request_payload

router = APIRouter(tags=["ledger"])


async def _prepare_idempotent_operation(
    *,
    request: Request,
    response: Response,
    idempotency_service: IdempotencyService,
    payload_hash: str,
    owner: str,
) -> tuple[str, Optional[TransactionResponse]]:
    key = request.headers.get("Idempotency-Key")
    if not key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key header required",
        )

    existing = await idempotency_service.get_key(key)
    if existing:
        if existing.request_hash != payload_hash:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Idempotency key conflict",
            )
        if (
            existing.response_code is not None
            and existing.response_body is not None
        ):
            response.status_code = existing.response_code
            cached = TransactionResponse.model_validate_json(existing.response_body)
            return key, cached

    try:
        await idempotency_service.acquire_lock(
            key=key,
            request_hash=payload_hash,
            owner=owner,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Idempotency key conflict",
        ) from exc

    return key, None


@router.post("/deposit", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def deposit_funds(
    payload: DepositRequest,
    request: Request,
    response: Response,
    idempotency_service: IdempotencyService = Depends(get_idempotency_service),
) -> TransactionResponse:
    session: AsyncSession = idempotency_service.session
    payload_hash = hash_request_payload(payload.model_dump(mode="json"))
    idempotency_key, cached = await _prepare_idempotent_operation(
        request=request,
        response=response,
        idempotency_service=idempotency_service,
        payload_hash=payload_hash,
        owner="POST:/deposit",
    )
    if cached:
        return cached

    ledger_service = LedgerService(session)

    try:
        transaction = await ledger_service.deposit(
            user_id=payload.user_id,
            amount=payload.amount,
            currency=payload.currency,
            description=payload.description,
            reference=payload.reference,
        )
        transaction_schema = TransactionResponse.model_validate(transaction)
        await idempotency_service.store_response(
            idempotency_key,
            status.HTTP_201_CREATED,
            transaction_schema.model_dump_json(),
        )
        await session.commit()
    except ValueError as exc:
        await session.rollback()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - unexpected
        await session.rollback()
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process deposit",
        ) from exc

    response.status_code = status.HTTP_201_CREATED
    return transaction_schema


@router.post("/transfer", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def transfer_funds(
    payload: TransferRequest,
    request: Request,
    response: Response,
    idempotency_service: IdempotencyService = Depends(get_idempotency_service),
) -> TransactionResponse:
    session: AsyncSession = idempotency_service.session
    payload_hash = hash_request_payload(payload.model_dump(mode="json"))
    idempotency_key, cached = await _prepare_idempotent_operation(
        request=request,
        response=response,
        idempotency_service=idempotency_service,
        payload_hash=payload_hash,
        owner="POST:/transfer",
    )
    if cached:
        return cached

    ledger_service = LedgerService(session)
    account_service = ledger_service.account_service

    try:
        source_account = await account_service.get_or_create_user_account(
            user_id=payload.source_user_id,
            currency=payload.currency,
        )
        destination_account = await account_service.get_or_create_user_account(
            user_id=payload.destination_user_id,
            currency=payload.currency,
        )

        transaction = await ledger_service.transfer(
            source_account_id=source_account.id,
            destination_account_id=destination_account.id,
            amount=payload.amount,
            currency=payload.currency,
            description=payload.description,
            reference=payload.reference,
        )
        transaction_schema = TransactionResponse.model_validate(transaction)
        await idempotency_service.store_response(
            idempotency_key,
            status.HTTP_201_CREATED,
            transaction_schema.model_dump_json(),
        )
        await session.commit()
    except ValueError as exc:
        await session.rollback()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - unexpected
        await session.rollback()
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process transfer",
        ) from exc

    response.status_code = status.HTTP_201_CREATED
    return transaction_schema


@router.post("/withdraw", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def withdraw_funds(
    payload: WithdrawalRequest,
    request: Request,
    response: Response,
    idempotency_service: IdempotencyService = Depends(get_idempotency_service),
) -> TransactionResponse:
    session: AsyncSession = idempotency_service.session
    payload_hash = hash_request_payload(payload.model_dump(mode="json"))
    idempotency_key, cached = await _prepare_idempotent_operation(
        request=request,
        response=response,
        idempotency_service=idempotency_service,
        payload_hash=payload_hash,
        owner="POST:/withdraw",
    )
    if cached:
        return cached

    ledger_service = LedgerService(session)

    try:
        transaction = await ledger_service.withdraw(
            user_id=payload.user_id,
            amount=payload.amount,
            currency=payload.currency,
            description=payload.description,
            reference=payload.reference,
        )
        transaction_schema = TransactionResponse.model_validate(transaction)
        await idempotency_service.store_response(
            idempotency_key,
            status.HTTP_201_CREATED,
            transaction_schema.model_dump_json(),
        )
        await session.commit()
    except ValueError as exc:
        await session.rollback()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - unexpected
        await session.rollback()
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process withdrawal",
        ) from exc

    response.status_code = status.HTTP_201_CREATED
    return transaction_schema


@router.get("/balance/{user_id}", response_model=UserBalanceResponse)
async def get_user_balance(
    user_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> UserBalanceResponse:
    account_service = AccountService(session)
    return await account_service.get_user_balance_summary(user_id)
