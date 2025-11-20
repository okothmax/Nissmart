"""Pydantic schemas for User resources."""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import EmailStr, Field

from app.schemas.base import APIModel, TimestampedModel


class UserCreate(APIModel):
    email: EmailStr = Field(description="Unique email address")
    full_name: str = Field(min_length=1, max_length=255)


class UserUpdate(APIModel):
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    is_active: Optional[bool] = None


class UserResponse(TimestampedModel):
    email: EmailStr
    full_name: str
    is_active: bool


class UserListResponse(APIModel):
    items: list[UserResponse]
    total: int


class UserSelectItem(APIModel):
    id: UUID
    full_name: str
    email: EmailStr
