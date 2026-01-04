"""
Database Migration: Add label_embedding column
Adds vector embedding column for label-level search
"""

import sys
from pathlib import Path
import asyncio

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.models.db_session import engine
from sqlalchemy import text


async def migrate():
    """Add label_embedding column to drug_labels table"""
    
    print("=" * 60)
    print("🔄 DATABASE MIGRATION")
    print("Adding label_embedding column to drug_labels table")
    print("=" * 60)
    print()
    
    async with engine.begin() as conn:
        # Check if column already exists
        print("Checking if column already exists...")
        result = await conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='drug_labels' AND column_name='label_embedding'
        """))
        
        exists = result.fetchone()
        
        if exists:
            print("✅ Column 'label_embedding' already exists")
            return
        
        # Add the column
        print("Adding label_embedding column...")
        await conn.execute(text("""
            ALTER TABLE drug_labels 
            ADD COLUMN label_embedding vector(384)
        """))
        
        # Create index for vector similarity search
        print("Creating vector similarity index...")
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_drug_label_embedding 
            ON drug_labels 
            USING ivfflat (label_embedding vector_cosine_ops)
            WITH (lists = 10)
        """))
        
        print()
        print("=" * 60)
        print("✅ MIGRATION SUCCESSFUL")
        print("=" * 60)
        print()
        print("Added:")
        print("  • label_embedding column (vector(384))")
        print("  • Vector similarity index (IVFFlat)")


if __name__ == "__main__":
    try:
        asyncio.run(migrate())
    except KeyboardInterrupt:
        print("\n\n⚠️  Migration interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ MIGRATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
