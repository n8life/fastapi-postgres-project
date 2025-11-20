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


def read_secret_file(file_path: str) -> str:
    """Read secret from file, stripping whitespace"""
    try:
        with open(file_path, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        raise FileNotFoundError(f"Secret file not found: {file_path}")
    except Exception as e:
        raise RuntimeError(f"Error reading secret file {file_path}: {e}")


class DatabaseManager:
    def __init__(self):
        self.engine: Optional[AsyncEngine] = None
        self.session_factory: Optional[async_sessionmaker[AsyncSession]] = None

    async def create_pool(self):
        """Create database connection pool"""
        # Try to read password from file first (for Kubernetes/production)
        postgres_password = None
        postgres_password_file = os.getenv("POSTGRES_PASSWORD_FILE")
        if postgres_password_file:
            try:
                postgres_password = read_secret_file(postgres_password_file)
            except Exception as e:
                print(f"Warning: Could not read password from file {postgres_password_file}: {e}")
        
        # Fall back to environment variable
        if not postgres_password:
            postgres_password = os.getenv("POSTGRES_PASSWORD")
        
        # Build database URL
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            # Construct URL with file-based or env-based password
            if postgres_password:
                db_host = os.getenv("DB_HOST", "localhost")
                db_port = os.getenv("DB_PORT", "5432")
                db_name = os.getenv("DB_NAME", "testdb")
                db_user = os.getenv("DB_USER", "postgres")
                database_url = f"postgresql+asyncpg://{db_user}:{postgres_password}@{db_host}:{db_port}/{db_name}"
            else:
                # Final fallback for development
                database_url = "postgresql+asyncpg://postgres:************@localhost:5432/testdb"
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
