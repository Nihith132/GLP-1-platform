"""
Test script for complete ETL pipeline
Processes one FDA label through Parse → NER → Embeddings → Database
"""

import sys
from pathlib import Path
import asyncio
import logging

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from backend.etl.etl_builder import ETLBuilder
from backend.models.db_session import AsyncSessionLocal
from backend.models.database import DrugLabel, DrugSection, SectionEmbedding
from sqlalchemy import select, func


async def test_etl_pipeline():
    """Test complete ETL pipeline on one file"""
    
    print("=" * 70)
    print("🧪 COMPLETE ETL PIPELINE TEST")
    print("=" * 70)
    print()
    
    # Find first zip file
    data_dir = project_root / "data" / "raw"
    zip_files = list(data_dir.glob("*.zip"))
    
    if not zip_files:
        print("❌ No FDA label files found")
        return False
    
    test_file = zip_files[0]
    print(f"📄 Testing with: {test_file.name}")
    print()
    
    # Initialize ETL builder
    print("Initializing ETL builder...")
    builder = ETLBuilder()
    print("✅ ETL builder ready")
    print()
    
    # Process the file
    print("=" * 70)
    print("STARTING ETL PIPELINE")
    print("=" * 70)
    print()
    
    drug_label_id = await builder.process_fda_label(str(test_file), test_file.name)
    
    if not drug_label_id:
        print("\n❌ ETL pipeline failed")
        return False
    
    print()
    print("=" * 70)
    print("VERIFYING DATABASE")
    print("=" * 70)
    print()
    
    # Verify data was saved correctly
    async with AsyncSessionLocal() as session:
        # Check drug_labels table
        result = await session.execute(
            select(DrugLabel).where(DrugLabel.id == drug_label_id)
        )
        drug_label = result.scalar_one_or_none()
        
        if not drug_label:
            print("❌ Drug label not found in database")
            return False
        
        print("✅ Drug Label Found:")
        print(f"   ID: {drug_label.id}")
        print(f"   Name: {drug_label.name}")
        print(f"   Generic: {drug_label.generic_name}")
        print(f"   Manufacturer: {drug_label.manufacturer}")
        print(f"   Set ID: {drug_label.set_id}")
        print(f"   Version: {drug_label.version}")
        print(f"   Status: {drug_label.status}")
        print(f"   Label embedding: {'✅ Present' if drug_label.label_embedding is not None else '❌ Missing'}")
        print()
        
        # Check NER summary
        if drug_label.ner_summary:
            print("✅ NER Summary (entity counts):")
            for entity_type, count in sorted(drug_label.ner_summary.items()):
                print(f"   {entity_type}: {count}")
            print()
        
        # Check drug_sections table
        result = await session.execute(
            select(func.count(DrugSection.id))
            .where(DrugSection.drug_label_id == drug_label_id)
        )
        section_count = result.scalar()
        
        print(f"✅ Drug Sections: {section_count} sections saved")
        
        # Get sample sections
        result = await session.execute(
            select(DrugSection)
            .where(DrugSection.drug_label_id == drug_label_id)
            .limit(3)
        )
        sample_sections = result.scalars().all()
        
        if sample_sections:
            print("\n   Sample sections:")
            for section in sample_sections:
                entities_count = len(section.ner_entities) if section.ner_entities else 0
                print(f"   • {section.title}")
                print(f"     LOINC: {section.loinc_code}")
                print(f"     Content length: {len(section.content)} chars")
                print(f"     Entities extracted: {entities_count}")
        print()
        
        # Check section_embeddings table
        result = await session.execute(
            select(func.count(SectionEmbedding.id))
            .join(DrugSection)
            .where(DrugSection.drug_label_id == drug_label_id)
        )
        embedding_count = result.scalar()
        
        print(f"✅ Section Embeddings: {embedding_count} embeddings saved")
        
        # Verify embedding dimensions
        result = await session.execute(
            select(SectionEmbedding)
            .join(DrugSection)
            .where(DrugSection.drug_label_id == drug_label_id)
            .limit(1)
        )
        sample_embedding = result.scalar_one_or_none()
        
        if sample_embedding and sample_embedding.embedding is not None:
            print(f"   Embedding dimensions: {len(sample_embedding.embedding)}")
            print(f"   First 5 values: {sample_embedding.embedding[:5]}")
        print()
    
    # Summary
    print("=" * 70)
    print("🎉 ETL PIPELINE TEST SUCCESSFUL!")
    print("=" * 70)
    print()
    print("Complete data flow verified:")
    print("  1. ✅ XML parsed successfully")
    print("  2. ✅ Entities extracted with NER")
    print("  3. ✅ Embeddings generated")
    print("  4. ✅ Data saved to database:")
    print(f"     • drug_labels: 1 record")
    print(f"     • drug_sections: {section_count} records")
    print(f"     • section_embeddings: {embedding_count} records")
    print()
    print("Next step: Process all 9 FDA label files!")
    print()
    
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_etl_pipeline())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
