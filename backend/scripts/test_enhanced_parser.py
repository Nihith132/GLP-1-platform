"""
Test script using ENHANCED parser with full SPL structure preservation
Creates rich, document-like HTML with proper hierarchy
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from etl.parser_enhanced import EnhancedFDAParser
from models.db_session import AsyncSessionLocal
from models.database import DrugLabel, DrugSection as DBDrugSection
import asyncio
from sqlalchemy import select


async def test_enhanced_parser():
    """Test enhanced parser with one label"""
    
    zip_file = '/Users/nihithreddy/slickbit label analyzer/data/raw/20230419_375bfe83-c893-3ea7-e054-00144ff88e88.zip'
    
    print("📦 Testing ENHANCED Parser")
    print(f"   File: {Path(zip_file).name}\n")
    
    # Parse with enhanced parser
    parser = EnhancedFDAParser()
    result = parser.parse_zip_file(zip_file)
    
    if not result:
        print("❌ Failed to parse")
        return
    
    metadata = result['metadata']
    sections = result['sections']
    
    print("✅ Parsed successfully with ENHANCED structure!")
    print(f"   Drug: {metadata['name']}")
    print(f"   SET ID: {metadata['set_id']}")
    print(f"   Sections: {len(sections)}\n")
    
    # Show section structure
    for i, section in enumerate(sections[:3], 1):  # Show first 3
        print(f"{i}. {section['title']}")
        if section.get('subsections'):
            print(f"   └─ {len(section['subsections'])} subsections")
        print(f"   Content length: {len(section['content'])} chars")
    
    if len(sections) > 3:
        print(f"... and {len(sections) - 3} more sections\n")
    
    # Show HTML sample
    first_section = sections[0]
    print(f"\n📄 Sample HTML from '{first_section['title']}':")
    print("=" * 70)
    print(first_section['content'][:800])
    print("=" * 70)
    
    # Update database
    async with AsyncSessionLocal() as session:
        # Find drug by SET ID
        query = select(DrugLabel).where(DrugLabel.set_id == metadata['set_id'])
        result_db = await session.execute(query)
        drug = result_db.scalar_one_or_none()
        
        if not drug:
            print(f"\n⚠️  Drug not found in database (SET ID: {metadata['set_id']})")
            return
        
        print(f"\n🔄 Updating database with ENHANCED HTML...")
        print(f"   Drug ID: {drug.id}")
        print(f"   Name: {drug.name}\n")
        
        # Update sections
        updated = 0
        for section in sections:
            section_query = select(DBDrugSection).where(
                DBDrugSection.drug_label_id == drug.id,
                DBDrugSection.loinc_code == section['loinc_code']
            )
            section_result = await session.execute(section_query)
            db_section = section_result.scalar_one_or_none()
            
            if db_section:
                db_section.content = section['content']
                updated += 1
                print(f"   ✓ Updated: {section['title']}")
        
        await session.commit()
        
        print(f"\n✅ Successfully updated {updated} sections with ENHANCED HTML!")
        print(f"\n🌐 View in browser: http://localhost:3001/analysis/{drug.id}")
        print(f"\n💡 Key improvements:")
        print(f"   • Proper <p>, <ul>, <ol>, <table> tags")
        print(f"   • Preserved styling (<strong>, <em>, <u>)")
        print(f"   • Table formatting with borders")
        print(f"   • Hierarchical structure maintained")
        print(f"   • Professional document presentation")


if __name__ == "__main__":
    asyncio.run(test_enhanced_parser())
