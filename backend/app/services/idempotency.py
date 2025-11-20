"""Utilities for managing idempotent API requests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from loguru import logger
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.idempotency import IdempotencyKey


class IdempotencyService:
    """Persists idempotency keys and cached responses."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.settings = get_settings()

    async def get_key(self, key: str) -> Optional[IdempotencyKey]:
        stmt = select(IdempotencyKey).where(IdempotencyKey.key == key)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def acquire_lock(self, key: str, request_hash: str, owner: str) -> IdempotencyKey:
        """Create or lock an idempotency key for processing."""

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=self.settings.idempotency_ttl_seconds)

        existing = await self.get_key(key)
        if existing:
            logger.debug("Found existing idempotency key for {key}", key=key)
            if existing.request_hash != request_hash and existing.response_body is None:
                raise ValueError("Idempotency key reuse with different payload")
            existing.locked_at = now
            existing.locked_by = owner
            existing.expires_at = expires_at
            existing.request_hash = request_hash
            return existing

        key_model = IdempotencyKey(
            key=key,
            request_hash=request_hash,
            locked_at=now,
            locked_by=owner,
            expires_at=expires_at,
        )
        self.session.add(key_model)
        await self.session.flush()
        return key_model

    async def store_response(
        self,
        key: str,
        response_code: int,
        response_body: str,
        recovery_point: str | None = None,
    ) -> None:
        stmt = (
            update(IdempotencyKey)
            .where(IdempotencyKey.key == key)
            .values(
                response_code=response_code,
                response_body=response_body,
                recovery_point=recovery_point,
                locked_at=None,
                locked_by=None,
            )
        )
        await self.session.execute(stmt)

    async def get_cached_response(self, key: str) -> Optional[tuple[int, str]]:
        record = await self.get_key(key)
        if record and record.response_code is not None and record.response_body is not None:
            return record.response_code, record.response_body
        return None
