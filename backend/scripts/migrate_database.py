"""
Database Migration Script
- Drops the unused approval_date column
- Updates last_updated column to use FDA effectiveTime instead of insert time
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from backend.models.db_session import AsyncSessionLocal


async def migrate_database():
    """Run database migrations"""
    
    print("\n" + "="*70)
    print("🔧 DATABASE MIGRATION")
    print("="*70 + "\n")
    
    async with AsyncSessionLocal() as session:
        try:
            # 1. Drop approval_date column
            print("1️⃣ Dropping unused 'approval_date' column...")
            await session.execute(text("""
                ALTER TABLE drug_labels 
                DROP COLUMN IF EXISTS approval_date;
            """))
            print("   ✅ Column dropped successfully\n")
            
            # 2. Update last_updated column comment
            print("2️⃣ Updating column metadata...")
            await session.execute(text("""
                COMMENT ON COLUMN drug_labels.last_updated IS 
                'FDA label publication date from effectiveTime field';
            """))
            await session.execute(text("""
                COMMENT ON COLUMN drug_labels.created_at IS 
                'When this record was inserted into our database';
            """))
            print("   ✅ Column comments updated\n")
            
            # Commit changes
            await session.commit()
            
            print("="*70)
            print("✅ MIGRATION COMPLETED SUCCESSFULLY")
            print("="*70 + "\n")
            
            # Show current schema
            print("📊 Current drug_labels columns:")
            result = await session.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'drug_labels'
                ORDER BY ordinal_position;
            """))
            
            for row in result:
                nullable = "NULL" if row[2] == "YES" else "NOT NULL"
                print(f"   • {row[0]:<25} {row[1]:<20} {nullable}")
            
            print()
            
        except Exception as e:
            await session.rollback()
            print(f"\n❌ Migration failed: {e}\n")
            raise


if __name__ == "__main__":
    asyncio.run(migrate_database())
