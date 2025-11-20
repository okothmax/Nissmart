"""Service layer for user operations."""

from __future__ import annotations

from typing import Sequence
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserCreate, UserResponse


class UserService:
    """Encapsulates user-related business logic."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(self, payload: UserCreate) -> User:
        user = User(email=payload.email, full_name=payload.full_name)
        self.session.add(user)
        try:
            await self.session.flush()
        except IntegrityError as exc:  # pragma: no cover - database constraint
            await self.session.rollback()
            raise ValueError("Email already exists") from exc
        return user

    async def get_user(self, user_id: UUID) -> User | None:
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_users(self, limit: int = 50, offset: int = 0) -> Sequence[User]:
        stmt = select(User).offset(offset).limit(limit).order_by(User.created_at.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count_users(self) -> int:
        stmt = select(func.count(User.id))
        result = await self.session.execute(stmt)
        return result.scalar_one()

    @staticmethod
    def to_schema(user: User) -> UserResponse:
        return UserResponse.model_validate(user)
