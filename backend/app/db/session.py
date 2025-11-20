"""Database engine and session management."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

_engine: AsyncEngine | None = None
_async_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Create (or return cached) async SQLAlchemy engine."""

    global _engine, _async_session_factory

    if _engine is None:
        settings = get_settings()
        connect_args = {}
        if settings.database_url.startswith("sqlite+aiosqlite"):
            connect_args["check_same_thread"] = False

        _engine = create_async_engine(
            settings.database_url,
            echo=settings.enable_sql_echo,
            connect_args=connect_args,
            pool_pre_ping=True,
        )

        _async_session_factory = async_sessionmaker(
            bind=_engine,
            expire_on_commit=False,
            autoflush=False,
        )

    assert _async_session_factory is not None, "Session factory must be initialized"
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the async session factory, creating it if needed."""

    get_engine()  # ensures initialization
    assert _async_session_factory is not None
    return _async_session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async database session."""

    session_factory = get_session_factory()
    async with session_factory() as session:
        yield session
