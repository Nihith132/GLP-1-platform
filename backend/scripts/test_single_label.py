"""
Test script to parse and update a single drug label with HTML structure
This will help verify the parser works correctly before updating all labels
"""
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from etl.parser import FDAXMLParser
from models.db_session import AsyncSessionLocal
from models.database import DrugLabel, DrugSection as DBDrugSection
import asyncio
from sqlalchemy import select

async def test_single_label():
    """Parse one label and update it in the database"""
    
    # Use the first available zip file
    zip_file = '/Users/nihithreddy/slickbit label analyzer/data/raw/20230419_375bfe83-c893-3ea7-e054-00144ff88e88.zip'
    
    print(f"📦 Testing with: {os.path.basename(zip_file)}")
    
    # Parse the label
    parser = FDAXMLParser()
    result = parser.parse_zip_file(zip_file)
    
    if not result:
        print("❌ Failed to parse label")
        return
    
    metadata = result['metadata']
    sections = result['sections']
    
    print(f"\n✓ Parsed successfully!")
    print(f"   Drug: {metadata['name']}")
    print(f"   SET ID: {metadata['set_id']}")
    print(f"   Sections: {len(sections)}")
    
    # Show sample of first section
    if sections:
        print(f"\n📄 First section HTML preview:")
        print(f"   Title: {sections[0]['title']}")
        print(f"   Content (first 300 chars):")
        print(f"   {sections[0]['content'][:300]}...")
    
    # Connect to database
    async with AsyncSessionLocal() as session:
        # Find the drug by SET ID
        query = select(DrugLabel).where(DrugLabel.set_id == metadata['set_id'])
        result = await session.execute(query)
        drug = result.scalar_one_or_none()
        
        if not drug:
            print(f"\n⚠️  Drug not found in database. SET ID: {metadata['set_id']}")
            print("   This label needs to be imported first.")
            return
        
        drug_id = drug.id
        drug_name = drug.name
        
        print(f"\n🔄 Updating drug in database...")
        print(f"   ID: {drug_id}")
        print(f"   Name: {drug_name}")
        
        # Update each section with HTML content
        for section in sections:
            # Find the section
            section_query = select(DBDrugSection).where(
                DBDrugSection.drug_label_id == drug_id,
                DBDrugSection.loinc_code == section['loinc_code']
            )
            section_result = await session.execute(section_query)
            db_section = section_result.scalar_one_or_none()
            
            if db_section:
                db_section.content = section['content']
        
        # Commit changes
        await session.commit()
        
        print(f"\n✅ Successfully updated {len(sections)} sections!")
        print(f"\n🌐 View in frontend: http://localhost:3001/analysis/{drug_id}")
        print(f"   Drug: {drug_name}")

if __name__ == "__main__":
    asyncio.run(test_single_label())
