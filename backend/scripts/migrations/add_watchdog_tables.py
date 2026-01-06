"""
Database Migration: Add Watchdog Tables and Columns
Adds drug_version_history table and version tracking columns to drugs table
"""

import asyncio
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from models.db_session import AsyncSessionLocal


async def add_watchdog_tables():
    """Add watchdog-related tables and columns"""
    
    async with AsyncSessionLocal() as session:
        try:
            print("Starting watchdog database migration...")
            
            # Step 1: Add columns to drug_labels table
            print("\n1. Adding version tracking columns to drug_labels table...")
            
            alter_drugs_queries = [
                # Current label version
                text("""
                    ALTER TABLE drug_labels 
                    ADD COLUMN IF NOT EXISTS current_label_version VARCHAR(50)
                """),
                
                # Enable/disable version checking per drug
                text("""
                    ALTER TABLE drug_labels 
                    ADD COLUMN IF NOT EXISTS version_check_enabled BOOLEAN DEFAULT false
                """),
                
                # Last time version was checked
                text("""
                    ALTER TABLE drug_labels 
                    ADD COLUMN IF NOT EXISTS last_version_check TIMESTAMP
                """)
            ]
            
            for query in alter_drugs_queries:
                await session.execute(query)
            
            print("   ✓ Columns added to drug_labels table")
            
            # Step 2: Create drug_version_history table
            print("\n2. Creating drug_version_history table...")
            
            create_history_table = text("""
                CREATE TABLE IF NOT EXISTS drug_version_history (
                    id SERIAL PRIMARY KEY,
                    drug_id INTEGER NOT NULL REFERENCES drug_labels(id) ON DELETE CASCADE,
                    old_version VARCHAR(50),
                    new_version VARCHAR(50) NOT NULL,
                    s3_key VARCHAR(500),
                    publish_date VARCHAR(50),
                    detected_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    processed BOOLEAN DEFAULT false,
                    notes TEXT
                )
            """)
            
            await session.execute(create_history_table)
            print("   ✓ drug_version_history table created")
            
            # Step 3: Create indexes for performance
            print("\n3. Creating indexes...")
            
            indexes = [
                text("""
                    CREATE INDEX IF NOT EXISTS idx_version_history_drug_id 
                    ON drug_version_history(drug_id)
                """),
                text("""
                    CREATE INDEX IF NOT EXISTS idx_version_history_detected_at 
                    ON drug_version_history(detected_at DESC)
                """),
                text("""
                    CREATE INDEX IF NOT EXISTS idx_drugs_version_check 
                    ON drug_labels(version_check_enabled) 
                    WHERE version_check_enabled = true
                """),
                text("""
                    CREATE INDEX IF NOT EXISTS idx_drugs_last_check 
                    ON drug_labels(last_version_check)
                """)
            ]
            
            for query in indexes:
                await session.execute(query)
            
            print("   ✓ Indexes created")
            
            # Commit all changes
            await session.commit()
            
            print("\n✅ Watchdog migration completed successfully!")
            print("\nNext steps:")
            print("1. Enable version checking for specific drugs:")
            print("   UPDATE drug_labels SET version_check_enabled = true WHERE set_id = 'your-set-id';")
            print("2. Set current version (optional, will auto-detect on first run):")
            print("   UPDATE drug_labels SET current_label_version = '1' WHERE set_id = 'your-set-id';")
            
        except Exception as e:
            await session.rollback()
            print(f"\n❌ Migration failed: {str(e)}")
            raise


if __name__ == "__main__":
    asyncio.run(add_watchdog_tables())
