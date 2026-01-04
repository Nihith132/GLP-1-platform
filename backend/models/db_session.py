"""
Database connection and session management
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from backend.core.config import settings
from backend.models.database import Base
import logging

logger = logging.getLogger(__name__)

# Convert postgresql:// to postgresql+asyncpg:// for async engine
database_url = settings.DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://')

# Create async engine
engine = create_async_engine(
    database_url,
    echo=settings.DEBUG,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,  # Verify connections before using
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    """
    Dependency for FastAPI to get database sessions
    Usage:
        @app.get("/endpoint")
        async def endpoint(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """
    Initialize database - create all tables
    Run this once at startup or via script
    """
    from sqlalchemy import text
    
    async with engine.begin() as conn:
        # Enable pgvector extension
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database tables created successfully")


async def drop_db():
    """
    Drop all tables - USE WITH CAUTION!
    Only for development/testing
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        logger.warning("All database tables dropped")
