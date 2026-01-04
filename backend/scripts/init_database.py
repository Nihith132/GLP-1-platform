"""
Database initialization script
Run this to set up the database schema
"""

import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.models.db_session import init_db, engine
from backend.core.config import settings


async def main():
    """Initialize database tables"""
    
    print("=" * 60)
    print("🗄️  DATABASE INITIALIZATION")
    print("=" * 60)
    print()
    
    # Display configuration
    db_url = settings.DATABASE_URL
    safe_url = db_url.split('@')[1] if '@' in db_url else 'hidden'
    print("📋 Configuration:")
    print(f"   Database: {safe_url.split(':')[0] if ':' in safe_url else safe_url}")
    print()
    
    try:
        print("Creating database tables...")
        await init_db()
        print("   ✅ Tables created successfully!")
        print()
        
        # List created tables
        print("📊 Database schema:")
        print("   • drug_labels")
        print("   • drug_sections")
        print("   • section_embeddings (with pgvector)")
        print("   • processing_logs")
        print()
        
        print("=" * 60)
        print("🎉 DATABASE READY!")
        print("=" * 60)
        print()
        print("Next step: Run the ETL pipeline to process FDA files")
        
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        await engine.dispose()
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
