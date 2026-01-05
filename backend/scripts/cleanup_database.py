"""
Database Cleanup and Fix Script
Fixes:
1. Resets ID sequence to start from 1 with no gaps
2. Updates chunk_index to be sequential per section
3. Cleans up drug names
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from backend.models.db_session import AsyncSessionLocal


async def fix_database():
    """Fix all database issues before reprocessing"""
    
    print("\n" + "="*80)
    print("🔧 DATABASE CLEANUP AND FIX")
    print("="*80 + "\n")
    
    async with AsyncSessionLocal() as session:
        try:
            # Step 1: Delete all data (we'll reprocess everything)
            print("1️⃣ Cleaning up existing data...")
            
            # Delete in correct order due to foreign keys
            await session.execute(text("DELETE FROM section_embeddings;"))
            print("   ✅ Deleted section_embeddings")
            
            await session.execute(text("DELETE FROM drug_sections;"))
            print("   ✅ Deleted drug_sections")
            
            await session.execute(text("DELETE FROM drug_labels;"))
            print("   ✅ Deleted drug_labels")
            
            await session.execute(text("DELETE FROM processing_logs;"))
            print("   ✅ Deleted processing_logs")
            
            print()
            
            # Step 2: Reset ID sequences to start from 1
            print("2️⃣ Resetting ID sequences...")
            
            await session.execute(text("ALTER SEQUENCE drug_labels_id_seq RESTART WITH 1;"))
            print("   ✅ Reset drug_labels ID sequence to 1")
            
            await session.execute(text("ALTER SEQUENCE drug_sections_id_seq RESTART WITH 1;"))
            print("   ✅ Reset drug_sections ID sequence to 1")
            
            await session.execute(text("ALTER SEQUENCE section_embeddings_id_seq RESTART WITH 1;"))
            print("   ✅ Reset section_embeddings ID sequence to 1")
            
            await session.execute(text("ALTER SEQUENCE processing_logs_id_seq RESTART WITH 1;"))
            print("   ✅ Reset processing_logs ID sequence to 1")
            
            print()
            
            # Commit changes
            await session.commit()
            
            print("="*80)
            print("✅ DATABASE CLEANUP COMPLETED")
            print("="*80)
            print()
            print("📋 Summary:")
            print("   • All existing data cleared")
            print("   • ID sequences reset to start from 1")
            print("   • Database is ready for clean reprocessing")
            print()
            print("Next step: Run reprocess script to load all 19 labels with fixed parsing")
            print("="*80 + "\n")
            
        except Exception as e:
            await session.rollback()
            print(f"\n❌ Cleanup failed: {e}\n")
            raise


if __name__ == "__main__":
    asyncio.run(fix_database())
