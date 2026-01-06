"""Drop redundant current_label_version column"""
import asyncio
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from models.db_session import AsyncSessionLocal

async def remove_column():
    async with AsyncSessionLocal() as session:
        try:
            print("Removing redundant current_label_version column...")
            await session.execute(text("ALTER TABLE drug_labels DROP COLUMN IF EXISTS current_label_version"))
            await session.commit()
            print("✅ Column removed successfully!")
        except Exception as e:
            await session.rollback()
            print(f"❌ Failed: {e}")

if __name__ == "__main__":
    asyncio.run(remove_column())
