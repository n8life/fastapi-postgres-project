import asyncpg
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator


class DatabaseManager:
    def __init__(self):
        self.pool = None
    
    async def create_pool(self):
        """Create database connection pool"""
        database_url = os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:************@localhost:5432/testdb"
        )
        self.pool = await asyncpg.create_pool(database_url)
        
        # Create table if it doesn't exist
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert sample data if table is empty
            count = await conn.fetchval("SELECT COUNT(*) FROM users")
            if count == 0:
                await conn.execute("""
                    INSERT INTO users (name, email) VALUES
                    ('John Doe', 'john@example.com'),
                    ('Jane Smith', 'jane@example.com'),
                    ('Bob Johnson', 'bob@example.com')
                """)
    
    async def close_pool(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
    
    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[asyncpg.Connection, None]:
        """Get database connection from pool"""
        async with self.pool.acquire() as conn:
            yield conn


# Global database manager instance
db_manager = DatabaseManager()


async def get_user_by_id(user_id: int) -> dict | None:
    """Get a user by ID from the database"""
    async with db_manager.get_connection() as conn:
        row = await conn.fetchrow(
            "SELECT id, name, email, created_at FROM users WHERE id = $1",
            user_id
        )
        if row:
            return {
                "id": row["id"],
                "name": row["name"],
                "email": row["email"],
                "created_at": row["created_at"].isoformat()
            }
        return None