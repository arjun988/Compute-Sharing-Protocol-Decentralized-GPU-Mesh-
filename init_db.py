"""
Initialize database tables
"""
import asyncio
from app.database import engine, Base
from app.config import settings


async def init_db():
    """Create all database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database initialized successfully!")


if __name__ == "__main__":
    asyncio.run(init_db())

