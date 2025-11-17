"""Database configuration and session management.

Uses SQLAlchemy 2.0 with async support.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models.

    All database models inherit from this class.
    """


class Database:
    """Database connection and session management.

    Handles:
    - Engine creation
    - Session management
    - Connection pooling
    - SQLite optimizations

    Examples:
        db = Database("sqlite+aiosqlite:///data/context.db")
        await db.connect()

        async with db.session() as session:
            # Use session
            ...

        await db.disconnect()
    """

    def __init__(self, database_url: str, *, echo: bool = False):
        """Initialize database.

        Args:
            database_url: Database connection URL
            echo: Whether to echo SQL statements (for debugging)
        """
        self.database_url = database_url
        self.echo = echo
        self._engine: Any = None
        self._session_maker: Any = None

    async def connect(self) -> None:
        """Connect to database and create engine."""
        self._engine = create_async_engine(
            self.database_url,
            echo=self.echo,
            pool_pre_ping=True,  # Verify connections before using
            pool_recycle=3600,  # Recycle connections after 1 hour
        )

        # SQLite optimizations
        if self.database_url.startswith("sqlite"):

            @event.listens_for(self._engine.sync_engine, "connect")
            def set_sqlite_pragma(dbapi_conn: Any, connection_record: object) -> None:  # noqa: ARG001
                """Enable SQLite optimizations."""
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.execute("PRAGMA cache_size=-64000")  # 64MB cache
                cursor.close()

        self._session_maker = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def disconnect(self) -> None:
        """Disconnect from database and dispose engine."""
        if self._engine:
            await self._engine.dispose()

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session context manager.

        Yields:
            AsyncSession for database operations

        Examples:
            async with db.session() as session:
                result = await session.execute(select(User))
                await session.commit()
        """
        if not self._session_maker:
            msg = "Database not connected. Call connect() first."
            raise RuntimeError(msg)

        async with self._session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def create_tables(self) -> None:
        """Create all tables defined in models.

        This should only be used for development/testing.
        Production should use Alembic migrations.
        """
        if not self._engine:
            msg = "Database not connected. Call connect() first."
            raise RuntimeError(msg)

        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_tables(self) -> None:
        """Drop all tables.

        WARNING: This will delete all data!
        Only use for testing.
        """
        if not self._engine:
            msg = "Database not connected. Call connect() first."
            raise RuntimeError(msg)

        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
