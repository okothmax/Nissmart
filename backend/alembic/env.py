"""Alembic migration environment."""

from __future__ import annotations

import logging

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import get_settings
from app.db.base import Base
from app import models  # noqa: F401  # ensure model metadata is registered

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)
logger = logging.getLogger("alembic.env")

settings = get_settings()

def _get_sync_url() -> str:
    """Return a synchronous SQLAlchemy URL for Alembic."""

    if settings.sync_database_url:
        return settings.sync_database_url

    url = settings.database_url

    if url.startswith("sqlite+aiosqlite"):
        return url.replace("sqlite+aiosqlite", "sqlite", 1)

    if "+asyncpg" in url:
        return url.replace("+asyncpg", "", 1)

    return url


def get_metadata():
    return Base.metadata


def run_migrations_offline() -> None:
    url = _get_sync_url()
    context.configure(
        url=url,
        target_metadata=get_metadata(),
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        url=_get_sync_url(),
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=get_metadata(),
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
