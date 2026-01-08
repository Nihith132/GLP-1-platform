"""
Migration: Add reports tables
Run with: python scripts/migrations/add_reports_tables.py
"""

import asyncio
import sys
from pathlib import Path
from sqlalchemy import text

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.db_session import AsyncSessionLocal


async def run_migration():
    """Execute the reports tables migration"""
    print("🔄 Starting reports tables migration...")
    
    async with AsyncSessionLocal() as session:
        try:
            # Define SQL statements separately (asyncpg doesn't support multiple statements)
            statements = [
                # Main reports table
                """
                CREATE TABLE IF NOT EXISTS reports (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    report_type VARCHAR(20) NOT NULL CHECK (report_type IN ('analysis', 'comparison')),
                    title VARCHAR(500) NOT NULL,
                    type_category VARCHAR(100) NOT NULL,
                    description TEXT,
                    tags TEXT[],
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    last_modified TIMESTAMP NOT NULL DEFAULT NOW(),
                    workspace_state JSONB NOT NULL
                )
                """,
                # Flagged chats
                """
                CREATE TABLE IF NOT EXISTS report_flagged_chats (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    report_id UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    citations JSONB,
                    flagged_at TIMESTAMP NOT NULL DEFAULT NOW()
                )
                """,
                # Flagged summaries
                """
                CREATE TABLE IF NOT EXISTS report_flagged_summaries (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    report_id UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
                    summary_type VARCHAR(50) NOT NULL,
                    competitor_id INTEGER,
                    competitor_name VARCHAR(500),
                    content TEXT NOT NULL,
                    metadata JSONB,
                    flagged_at TIMESTAMP NOT NULL DEFAULT NOW()
                )
                """,
                # Highlights
                """
                CREATE TABLE IF NOT EXISTS report_highlights (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    report_id UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
                    drug_id INTEGER NOT NULL,
                    section_id INTEGER NOT NULL,
                    loinc_code VARCHAR(20) NOT NULL,
                    start_char INTEGER NOT NULL,
                    end_char INTEGER NOT NULL,
                    color VARCHAR(10) NOT NULL CHECK (color IN ('red', 'blue')),
                    annotation TEXT,
                    highlighted_text TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW()
                )
                """,
                # Quick notes
                """
                CREATE TABLE IF NOT EXISTS report_quick_notes (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    report_id UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
                    note_type VARCHAR(20) NOT NULL CHECK (note_type IN ('citation_linked', 'standalone')),
                    content TEXT NOT NULL CHECK (length(content) <= 500),
                    drug_id INTEGER,
                    drug_name VARCHAR(500),
                    section_id INTEGER,
                    section_title VARCHAR(500),
                    loinc_code VARCHAR(20),
                    highlighted_text TEXT,
                    start_char INTEGER,
                    end_char INTEGER,
                    highlight_color VARCHAR(10) CHECK (highlight_color IN ('red', 'blue')),
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
                )
                """,
                # Indexes
                "CREATE INDEX IF NOT EXISTS idx_reports_created_at ON reports(created_at DESC)",
                "CREATE INDEX IF NOT EXISTS idx_reports_type ON reports(report_type)",
                "CREATE INDEX IF NOT EXISTS idx_reports_modified ON reports(last_modified DESC)",
                "CREATE INDEX IF NOT EXISTS idx_reports_tags ON reports USING GIN(tags)",
                "CREATE INDEX IF NOT EXISTS idx_flagged_chats_report ON report_flagged_chats(report_id)",
                "CREATE INDEX IF NOT EXISTS idx_flagged_summaries_report ON report_flagged_summaries(report_id)",
                "CREATE INDEX IF NOT EXISTS idx_highlights_report ON report_highlights(report_id)",
                "CREATE INDEX IF NOT EXISTS idx_quick_notes_report ON report_quick_notes(report_id)",
                "CREATE INDEX IF NOT EXISTS idx_quick_notes_type ON report_quick_notes(report_id, note_type)"
            ]
            
            # Execute each statement separately
            for stmt in statements:
                await session.execute(text(stmt))
            
            await session.commit()
            
            print("✅ Reports tables created successfully!")
            print("\nCreated tables:")
            print("  • reports")
            print("  • report_flagged_chats")
            print("  • report_flagged_summaries")
            print("  • report_highlights")
            print("  • report_quick_notes")
            print("\nCreated indexes:")
            print("  • Performance indexes on all tables")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Migration failed: {str(e)}")
            raise


async def verify_migration():
    """Verify tables were created"""
    print("\n🔍 Verifying migration...")
    
    async with AsyncSessionLocal() as session:
        # Check if tables exist
        result = await session.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE 'report%'
            ORDER BY table_name
        """))
        
        tables = [row[0] for row in result.fetchall()]
        
        if len(tables) == 5:
            print(f"✅ Verified: All 5 tables exist")
            for table in tables:
                print(f"   ✓ {table}")
        else:
            print(f"⚠️  Warning: Expected 5 tables, found {len(tables)}")


if __name__ == "__main__":
    asyncio.run(run_migration())
    asyncio.run(verify_migration())
