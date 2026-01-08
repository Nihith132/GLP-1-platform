"""
Enable all 19 drugs for automated version monitoring
"""

import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres.ydslktnlmxgryngjzast:nicduk-xEpwid-tusbe8@aws-1-eu-north-1.pooler.supabase.com:5432/postgres')
engine = create_async_engine(DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://'))
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def enable_all_drugs():
    """Enable version checking for all 19 drugs"""
    
    async with async_session_maker() as session:
        # Enable all drugs
        query = text("""
            UPDATE drug_labels
            SET version_check_enabled = true
            WHERE version_check_enabled = false OR version_check_enabled IS NULL
        """)
        
        result = await session.execute(query)
        await session.commit()
        
        print(f"✅ Enabled {result.rowcount} drugs for monitoring")
        
        # Verify
        verify_query = text("""
            SELECT name, set_id, version, version_check_enabled
            FROM drug_labels
            ORDER BY name
        """)
        
        verify_result = await session.execute(verify_query)
        drugs = verify_result.fetchall()
        
        print(f"\n📋 All {len(drugs)} Drugs Status:")
        print("=" * 80)
        for drug in drugs:
            status = "✅ ENABLED" if drug[3] else "❌ DISABLED"
            print(f"{status} | {drug[0]:<35} | Version: {drug[2]}")
        
        # Summary
        enabled_count = sum(1 for d in drugs if d[3])
        print("=" * 80)
        print(f"\n✅ Total Enabled: {enabled_count}/{len(drugs)}")


if __name__ == "__main__":
    asyncio.run(enable_all_drugs())
