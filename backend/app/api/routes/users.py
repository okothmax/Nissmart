"""User API routes."""

from __future__ import annotations

import json
from typing import Sequence
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_idempotency_service
from app.schemas.user import (
    UserCreate,
    UserListResponse,
    UserResponse,
)
from app.services.idempotency import IdempotencyService
from app.services.user_service import UserService
from app.utils.hash_utils import hash_request_payload

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    request: Request,
    response: Response,
    idempotency_service: IdempotencyService = Depends(get_idempotency_service),
) -> UserResponse:
    idempotency_key = request.headers.get("Idempotency-Key")
    if not idempotency_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key header required",
        )

    payload_hash = hash_request_payload(payload.model_dump())
    session = idempotency_service.session
    user_service = UserService(session)

    existing_key = await idempotency_service.get_key(idempotency_key)
    if existing_key:
        if existing_key.request_hash != payload_hash:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Idempotency key conflict",
            )
        if (
            existing_key.response_code is not None
            and existing_key.response_body is not None
        ):
            response.status_code = existing_key.response_code
            return UserResponse.model_validate_json(existing_key.response_body)

    try:
        await idempotency_service.acquire_lock(
            key=idempotency_key,
            request_hash=payload_hash,
            owner="POST:/users",
        )
    except ValueError as exc:  # conflicting payload
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Idempotency key conflict",
        ) from exc

    try:
        user = await user_service.create_user(payload)
    except ValueError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    user_schema = UserService.to_schema(user)

    await idempotency_service.store_response(
        idempotency_key,
        status.HTTP_201_CREATED,
        user_schema.model_dump_json(),
    )
    await session.commit()

    response.status_code = status.HTTP_201_CREATED
    return user_schema


@router.get("", response_model=UserListResponse)
async def list_users(
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_db),
) -> UserListResponse:
    user_service = UserService(session)
    users: Sequence = await user_service.list_users(limit=limit, offset=offset)
    total = await user_service.count_users()
    items = [UserService.to_schema(user) for user in users]
    return UserListResponse(items=items, total=total)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> UserResponse:
    user_service = UserService(session)
    user = await user_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserService.to_schema(user)
