"""FastAPI dependency helpers."""

from __future__ import annotations

from typing import AsyncGenerator

from fastapi import Depends

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.services.idempotency import IdempotencyService


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db_session():
        yield session


async def get_idempotency_service(
    session: AsyncSession = Depends(get_db),
) -> IdempotencyService:
    return IdempotencyService(session)
