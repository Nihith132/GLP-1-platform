"""
Database connection and session management
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from models.database import Base
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from root directory
root_dir = Path(__file__).parent.parent.parent
env_path = root_dir / '.env'
load_dotenv(dotenv_path=env_path)

logger = logging.getLogger(__name__)

# Get database URL from environment
database_url = os.getenv('DATABASE_URL', 'postgresql://localhost/glp1_labels')
logger.info(f"Loading .env from: {env_path}")
logger.info(f"DATABASE_URL loaded: {database_url[:50]}...")  # Log first 50 chars

# Convert postgresql:// to postgresql+asyncpg:// for async engine
if database_url.startswith('postgresql://'):
    database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://')

# Create async engine
engine = create_async_engine(
    database_url,
    echo=os.getenv('DEBUG', 'False').lower() == 'true',
    pool_size=int(os.getenv('DATABASE_POOL_SIZE', '10')),
    max_overflow=int(os.getenv('DATABASE_MAX_OVERFLOW', '20')),
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
