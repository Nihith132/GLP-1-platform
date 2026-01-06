"""Enable SAXENDA for version monitoring"""
import asyncio
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from models.db_session import AsyncSessionLocal

async def enable_saxenda():
    async with AsyncSessionLocal() as session:
        try:
            print("Enabling SAXENDA for version monitoring...")
            
            # Enable version checking for SAXENDA
            await session.execute(text("""
                UPDATE drug_labels 
                SET version_check_enabled = true
                WHERE set_id = '2160dee6-dc44-4639-af3f-fd1ac2a32d15'
            """))
            
            await session.commit()
            
            # Verify
            result = await session.execute(text("""
                SELECT name, set_id, version, version_check_enabled 
                FROM drug_labels 
                WHERE version_check_enabled = true
            """))
            
            rows = result.fetchall()
            if rows:
                print("\n✅ SAXENDA enabled successfully!")
                print("\nEnabled drugs:")
                for row in rows:
                    print(f"   • {row.name} (SET_ID: {row.set_id}, Version: {row.version})")
            else:
                print("⚠️  No drugs enabled. Check if SET_ID exists.")
                
        except Exception as e:
            await session.rollback()
            print(f"❌ Failed: {e}")

if __name__ == "__main__":
    asyncio.run(enable_saxenda())
