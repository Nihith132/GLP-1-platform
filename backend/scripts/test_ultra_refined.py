"""
Test ULTRA-REFINED parser with maximum information extraction
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from etl.parser_ultra_refined import UltraRefinedParser
from models.db_session import AsyncSessionLocal
from models.database import DrugLabel, DrugSection as DBDrugSection
import asyncio
from sqlalchemy import select


async def test_ultra_refined():
    """Test ultra-refined parser"""
    
    zip_file = '/Users/nihithreddy/slickbit label analyzer/data/raw/20230419_375bfe83-c893-3ea7-e054-00144ff88e88.zip'
    
    print("🚀 Testing ULTRA-REFINED Parser")
    print("=" * 70)
    print(f"File: {Path(zip_file).name}\n")
    
    # Parse
    parser = UltraRefinedParser()
    result = parser.parse_zip_file(zip_file)
    
    if not result:
        print("❌ Failed")
        return
    
    metadata = result['metadata']
    sections = result['sections']
    
    print("✅ ULTRA-REFINED PARSING COMPLETE!\n")
    print(f"📋 Drug Information:")
    print(f"   Name: {metadata['name']}")
    print(f"   Generic: {metadata.get('generic_name', 'N/A')}")
    print(f"   Manufacturer: {metadata.get('manufacturer', 'N/A')}")
    print(f"   Dosage Forms: {', '.join(metadata.get('dosage_forms', [])) or 'N/A'}")
    print(f"   Strengths: {', '.join(metadata.get('strengths', [])) or 'N/A'}")
    print(f"   Version: {metadata.get('version', 'N/A')}")
    print(f"   Last Updated: {metadata.get('last_updated', 'N/A')}\n")
    
    print(f"📑 Section Structure ({len(sections)} sections):")
    print("=" * 70)
    
    for section in sections:
        importance_icon = {
            'critical': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '⚪'
        }.get(section['importance'], '⚪')
        
        print(f"\n{importance_icon} [{section['section_number']}] {section['title']}")
        print(f"   Importance: {section['importance'].upper()}")
        print(f"   Type: {section['type']}")
        print(f"   Content: {len(section['content'])} chars")
        
        if section.get('subsections'):
            for sub in section['subsections']:
                print(f"      └─ [{sub['section_number']}] {sub['title']}")
    
    # Show HTML sample
    critical_section = next((s for s in sections if s['importance'] == 'critical'), sections[0])
    print(f"\n\n📄 Sample HTML from CRITICAL section: '{critical_section['title']}'")
    print("=" * 70)
    print(critical_section['content'][:1000])
    print("...")
    print("=" * 70)
    
    # Update database
    async with AsyncSessionLocal() as session:
        query = select(DrugLabel).where(DrugLabel.set_id == metadata['set_id'])
        result_db = await session.execute(query)
        drug = result_db.scalar_one_or_none()
        
        if not drug:
            print(f"\n⚠️  Drug not found in database")
            return
        
        print(f"\n🔄 Updating database with ULTRA-REFINED HTML...")
        print(f"   Drug ID: {drug.id}\n")
        
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
                importance_icon = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '⚪'}[section['importance']]
                print(f"   {importance_icon} [{section['section_number']}] {section['title']}")
        
        await session.commit()
        
        print(f"\n✅ Successfully updated {updated} sections!\n")
        print(f"🌐 View: http://localhost:3001/analysis/{drug.id}\n")
        print(f"💎 ULTRA-REFINED Features:")
        print(f"   ✓ Section numbering (1, 1.1, 1.2, etc.)")
        print(f"   ✓ Importance badges (Critical/High/Medium/Low)")
        print(f"   ✓ Semantic highlighting (warnings, dosages)")
        print(f"   ✓ Rich metadata (dosage forms, strengths)")
        print(f"   ✓ Context-aware styling")
        print(f"   ✓ Enhanced tables with gradients")
        print(f"   ✓ Keyword detection & highlighting")
        print(f"   ✓ Optimized for comparison")


if __name__ == "__main__":
    asyncio.run(test_ultra_refined())
