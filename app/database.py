import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from .models import Base, User


class DatabaseManager:
    def __init__(self):
        self.engine: Optional[AsyncEngine] = None
        self.session_factory: Optional[async_sessionmaker[AsyncSession]] = None

    async def create_pool(self):
        """Create database connection pool"""
        database_url = os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://postgres:************@localhost:5432/testdb"
        )
        self.engine = create_async_engine(
            database_url,
            pool_pre_ping=True,
            pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10")),
            echo=os.getenv("SQLALCHEMY_ECHO", "0") == "1",
        )
        self.session_factory = async_sessionmaker(
            self.engine, expire_on_commit=False
        )

        # Create tables
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Seed sample data if empty
        await self._ensure_sample_data()

    async def _ensure_sample_data(self) -> None:
        """Insert sample data if table is empty"""
        async with self.get_connection() as session:
            count = await session.scalar(select(func.count()).select_from(User))
            if not count:
                session.add_all(
                    [
                        User(name="John Doe", email="john@example.com"),
                        User(name="Jane Smith", email="jane@example.com"),
                        User(name="Bob Johnson", email="bob@example.com"),
                    ]
                )
                await session.commit()

    async def close_pool(self):
        """Close database connection pool"""
        if self.engine:
            await self.engine.dispose()
            self.engine = None
            self.session_factory = None

    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session from pool"""
        if not self.session_factory:
            raise RuntimeError("Database not initialized")
        async with self.session_factory() as session:
            yield session


# Global database manager instance
db_manager = DatabaseManager()


async def get_user_by_id(user_id: int) -> dict | None:
    """Get a user by ID from the database"""
    async with db_manager.get_connection() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            return {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "created_at": user.created_at.isoformat() if user.created_at else None,
            }
        return None
