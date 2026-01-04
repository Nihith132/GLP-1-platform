"""
Migration: Add unique constraint to prevent duplicate drug labels
Ensures (set_id, version) combination is unique
"""

import asyncio
from backend.models.db_session import engine
from sqlalchemy import text


async def add_unique_constraint():
    """Add unique constraint on (set_id, version)"""
    
    print("\n🔧 Adding unique constraint to drug_labels table...")
    print("=" * 60)
    
    async with engine.begin() as conn:
        # Create unique constraint on (set_id, version)
        await conn.execute(text("""
            ALTER TABLE drug_labels 
            ADD CONSTRAINT uq_drug_labels_set_version 
            UNIQUE (set_id, version);
        """))
        
        print("✅ Unique constraint added: uq_drug_labels_set_version")
        print("   This prevents duplicate entries with same SET_ID and Version")
    
    print("=" * 60)
    print("✅ Migration complete!\n")


if __name__ == "__main__":
    asyncio.run(add_unique_constraint())
