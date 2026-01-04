"""
Cleanup: Remove duplicate drug labels from database
Keeps the oldest entry for each (set_id, version) pair
"""

import asyncio
from backend.models.db_session import AsyncSessionLocal
from backend.models.database import DrugLabel
from sqlalchemy import select, func


async def cleanup_duplicates():
    """Remove duplicate drug labels, keeping the first one"""
    
    print("\n🧹 CLEANING UP DUPLICATE DRUG LABELS")
    print("=" * 60)
    
    async with AsyncSessionLocal() as session:
        # Find duplicates
        result = await session.execute(
            select(DrugLabel.set_id, DrugLabel.version, func.count(DrugLabel.id).label('count'))
            .group_by(DrugLabel.set_id, DrugLabel.version)
            .having(func.count(DrugLabel.id) > 1)
        )
        duplicates = result.all()
        
        if not duplicates:
            print("✅ No duplicates found!")
            return
        
        print(f"Found {len(duplicates)} duplicate groups:")
        
        total_deleted = 0
        
        for dup in duplicates:
            set_id, version, count = dup
            print(f"\n  SET_ID: {set_id}, Version: {version} ({count} entries)")
            
            # Get all records for this set_id/version, ordered by ID
            result = await session.execute(
                select(DrugLabel)
                .where(DrugLabel.set_id == set_id, DrugLabel.version == version)
                .order_by(DrugLabel.id)
            )
            records = result.scalars().all()
            
            # Keep the first one, delete the rest
            keep = records[0]
            delete = records[1:]
            
            print(f"  ✅ Keeping: ID {keep.id} - {keep.generic_name}")
            
            for record in delete:
                print(f"  ❌ Deleting: ID {record.id} - {record.generic_name}")
                await session.delete(record)
                total_deleted += 1
        
        # Commit changes
        await session.commit()
        
        print("\n" + "=" * 60)
        print(f"✅ Cleanup complete! Deleted {total_deleted} duplicate records")
        print("=" * 60 + "\n")
        
        # Show final count
        final_count = await session.scalar(select(func.count()).select_from(DrugLabel))
        print(f"📊 Final drug labels count: {final_count}\n")


if __name__ == "__main__":
    asyncio.run(cleanup_duplicates())
