"""
Verify database status after processing all labels
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.models.db_session import AsyncSessionLocal
from backend.models.database import DrugLabel, DrugSection, SectionEmbedding
from sqlalchemy import select, func


async def verify_database():
    """Check database counts and list all drugs"""
    
    async with AsyncSessionLocal() as session:
        # Count totals
        drug_count = await session.execute(select(func.count(DrugLabel.id)))
        total_drugs = drug_count.scalar()
        
        section_count = await session.execute(select(func.count(DrugSection.id)))
        total_sections = section_count.scalar()
        
        embedding_count = await session.execute(select(func.count(SectionEmbedding.id)))
        total_embeddings = embedding_count.scalar()
        
        # Get drug list
        result = await session.execute(
            select(
                DrugLabel.id,
                DrugLabel.generic_name,
                DrugLabel.manufacturer,
                DrugLabel.source_file
            ).order_by(DrugLabel.id)
        )
        
        drugs = result.all()
        
        print("\n" + "="*80)
        print("📊 FINAL DATABASE STATUS")
        print("="*80)
        print(f"✅ Total Drugs: {total_drugs}")
        print(f"✅ Total Sections: {total_sections}")
        print(f"✅ Total Embeddings: {total_embeddings}")
        print("="*80)
        print("\n📋 ALL DRUGS IN DATABASE:\n")
        
        for i, drug in enumerate(drugs, 1):
            generic = drug.generic_name or "N/A"
            manufacturer = drug.manufacturer or "N/A"
            print(f"{i:2}. [ID {drug.id:2}] {generic:35} | {manufacturer:35}")
            print(f"    File: {drug.source_file}")
            print()
        
        print("="*80)
        print("✅ DATABASE EXPANSION COMPLETE!")
        print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(verify_database())
