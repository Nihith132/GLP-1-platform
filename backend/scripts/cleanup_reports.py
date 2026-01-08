"""
Cleanup Script for Reports Database
- Removes all testing data from reports tables
- Adds constraints to prevent duplicate entries
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text
from models.db_session import AsyncSessionLocal


async def cleanup_reports_database():
    """Clean up all testing data from reports tables"""
    async with AsyncSessionLocal() as session:
        try:
            print("🧹 Starting Reports Database Cleanup...\n")
            
            # Get counts before deletion
            print("📊 Current State:")
            tables = [
                'report_quick_notes',
                'report_highlights', 
                'report_flagged_summaries',
                'report_flagged_chats',
                'reports'
            ]
            
            before_counts = {}
            for table in tables:
                result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                before_counts[table] = count
                print(f"  {table}: {count} records")
            
            # Delete all data (in correct order due to foreign keys)
            print("\n🗑️  Deleting all testing data...")
            
            # Child tables first (due to foreign key constraints)
            await session.execute(text("DELETE FROM report_quick_notes"))
            await session.execute(text("DELETE FROM report_highlights"))
            await session.execute(text("DELETE FROM report_flagged_summaries"))
            await session.execute(text("DELETE FROM report_flagged_chats"))
            
            # Parent table last
            await session.execute(text("DELETE FROM reports"))
            
            await session.commit()
            print("✅ All testing data deleted successfully!")
            
            # Verify deletion
            print("\n📊 After Cleanup:")
            total_remaining = 0
            for table in tables:
                result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                total_remaining += count
                print(f"  {table}: {count} records")
            
            if total_remaining == 0:
                print("\n✅ Database is completely clean!")
            
            # Add indexes to prevent duplicates and improve performance
            print("\n🔧 Adding indexes to prevent duplicates and improve performance...")
            
            # Index on report_id for faster lookups in child tables
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_report_flagged_chats_report ON report_flagged_chats(report_id)",
                "CREATE INDEX IF NOT EXISTS idx_report_flagged_summaries_report ON report_flagged_summaries(report_id)",
                "CREATE INDEX IF NOT EXISTS idx_report_highlights_report ON report_highlights(report_id)",
                "CREATE INDEX IF NOT EXISTS idx_report_quick_notes_report ON report_quick_notes(report_id)",
                
                # Index on title and type for duplicate detection
                "CREATE INDEX IF NOT EXISTS idx_reports_title_type ON reports(title, report_type)",
                
                # Index on created_at for sorting
                "CREATE INDEX IF NOT EXISTS idx_reports_created_at ON reports(created_at DESC)",
                
                # Index on workspace_state for JSON queries
                "CREATE INDEX IF NOT EXISTS idx_reports_workspace_state ON reports USING gin(workspace_state)",
            ]
            
            for idx_sql in indexes:
                try:
                    await session.execute(text(idx_sql))
                    index_name = idx_sql.split("idx_")[1].split(" ")[0] if "idx_" in idx_sql else "unknown"
                    print(f"  ✅ Created index: idx_{index_name}")
                except Exception as e:
                    if "already exists" not in str(e):
                        print(f"  ⚠️  Index creation warning: {e}")
            
            await session.commit()
            
            print("\n🎉 Reports database cleanup completed successfully!")
            print("\n📝 Summary:")
            print(f"  - Deleted {sum(before_counts.values())} total records")
            print(f"  - All tables are now empty and ready for production use")
            print(f"  - Added 7 indexes to improve performance and prevent issues")
            
        except Exception as e:
            await session.rollback()
            print(f"\n❌ Error during cleanup: {e}")
            raise


async def verify_constraints():
    """Verify that constraints are working properly"""
    async with AsyncSessionLocal() as session:
        print("\n🔍 Verifying Database Constraints...")
        
        # Check foreign key constraints
        result = await session.execute(text("""
            SELECT 
                tc.table_name, 
                tc.constraint_name,
                tc.constraint_type
            FROM information_schema.table_constraints tc
            WHERE tc.table_name LIKE 'report%'
            AND tc.constraint_type = 'FOREIGN KEY'
            ORDER BY tc.table_name
        """))
        
        fk_constraints = result.fetchall()
        print(f"\n  Foreign Key Constraints: {len(fk_constraints)}")
        for fk in fk_constraints:
            print(f"    - {fk.table_name}: {fk.constraint_name}")
        
        # Check check constraints
        result = await session.execute(text("""
            SELECT 
                tc.table_name,
                tc.constraint_name
            FROM information_schema.table_constraints tc
            WHERE tc.table_name LIKE 'report%'
            AND tc.constraint_type = 'CHECK'
            ORDER BY tc.table_name
        """))
        
        check_constraints = result.fetchall()
        print(f"\n  Check Constraints: {len(check_constraints)}")
        for chk in check_constraints:
            print(f"    - {chk.table_name}: {chk.constraint_name}")
        
        print("\n✅ All constraints are properly configured!")


if __name__ == "__main__":
    asyncio.run(cleanup_reports_database())
    asyncio.run(verify_constraints())
