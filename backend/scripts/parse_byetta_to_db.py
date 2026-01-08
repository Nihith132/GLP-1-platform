"""
Parse Byetta with hierarchical parser and save to database
Then you can view it in the frontend
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from datetime import datetime
from models.db_session import AsyncSessionLocal
from models.database import DrugLabel, DrugSection
from etl.parser_hierarchical import HierarchicalParser
from sqlalchemy import select, delete


async def parse_and_save_byetta():
    """Parse Byetta and save to database"""
    
    print("\n" + "="*80)
    print("📦 PARSING BYETTA WITH HIERARCHICAL PARSER")
    print("="*80 + "\n")
    
    # Parse Byetta
    data_dir = Path(__file__).parent.parent.parent / 'data' / 'raw'
    byetta_zip = data_dir / '20250906_53d03c03-ebf7-418d-88a8-533eabd2ee4f.zip'
    
    parser = HierarchicalParser()
    print(f"📁 Parsing: {byetta_zip.name}")
    result = parser.parse_zip_file(str(byetta_zip))
    
    if not result:
        print("❌ Parsing failed!")
        return False
    
    metadata = result['metadata']
    sections = result['sections']
    
    print(f"✅ Parsed successfully!")
    print(f"   - {len(sections)} sections")
    print(f"   - {len([s for s in sections if s['level'] == 1])} main sections")
    print(f"   - {len([s for s in sections if s['level'] > 1])} subsections")
    
    # Save to database
    print(f"\n💾 Saving to database...")
    
    async with AsyncSessionLocal() as session:
        try:
            # Check if Byetta already exists
            existing = await session.execute(
                select(DrugLabel).where(DrugLabel.name == "Byetta")
            )
            existing_drug = existing.scalar_one_or_none()
            
            if existing_drug:
                print(f"   Found existing Byetta (ID: {existing_drug.id})")
                print(f"   Deleting old sections...")
                
                # Delete old sections
                await session.execute(
                    delete(DrugSection).where(DrugSection.drug_label_id == existing_drug.id)
                )
                
                # Update metadata
                existing_drug.set_id = metadata['set_id']
                existing_drug.version = metadata['version']
                existing_drug.manufacturer = metadata['manufacturer']
                existing_drug.last_updated = datetime.utcnow()
                existing_drug.source_file = byetta_zip.name
                
                drug = existing_drug
                print(f"   Updated drug metadata")
            else:
                # Create new drug label
                drug = DrugLabel(
                    name="Byetta",
                    generic_name="exenatide",
                    manufacturer=metadata['manufacturer'],
                    set_id=metadata['set_id'],
                    version=metadata['version'],
                    is_current_version=True,
                    status="active",
                    last_updated=datetime.utcnow(),
                    source_file=byetta_zip.name
                )
                session.add(drug)
                await session.flush()  # Get the ID
                print(f"   Created new drug label (ID: {drug.id})")
            
            # Save sections with hierarchy
            print(f"   Saving {len(sections)} sections...")
            
            # First pass: save all sections without parent_id
            section_map = {}  # Map section_number to DB ID
            
            for section_data in sections:
                section = DrugSection(
                    drug_label_id=drug.id,
                    section_number=section_data['section_number'],
                    level=section_data['level'],
                    parent_section_id=None,  # Set in second pass
                    loinc_code=section_data.get('loinc_code'),
                    title=section_data['title'],
                    content=section_data['content'],
                    content_html=section_data.get('content_html', ''),
                    order=section_data.get('order', 0)
                )
                session.add(section)
                await session.flush()  # Get the ID
                
                # Store mapping
                section_map[section_data['section_number']] = section.id
            
            # Second pass: set parent_section_id
            print(f"   Setting parent-child relationships...")
            
            for section_data in sections:
                section_num = section_data['section_number']
                
                # Find parent section number (e.g., "1.2.3" -> parent is "1.2")
                if '.' in section_num:
                    parts = section_num.split('.')
                    parent_num = '.'.join(parts[:-1])
                    
                    if parent_num in section_map:
                        # Get the section from database and update parent_id
                        section_id = section_map[section_num]
                        result = await session.execute(
                            select(DrugSection).where(DrugSection.id == section_id)
                        )
                        section = result.scalar_one()
                        section.parent_section_id = section_map[parent_num]
            
            # Commit all changes
            await session.commit()
            
            print(f"\n✅ Successfully saved Byetta to database!")
            print(f"   Drug ID: {drug.id}")
            print(f"   Sections saved: {len(sections)}")
            print(f"   Hierarchy established: ✅")
            
            return True
            
        except Exception as e:
            await session.rollback()
            print(f"\n❌ Error saving to database: {e}")
            import traceback
            traceback.print_exc()
            return False


async def verify_data():
    """Verify the saved data"""
    
    print(f"\n" + "="*80)
    print("🔍 VERIFYING SAVED DATA")
    print("="*80 + "\n")
    
    async with AsyncSessionLocal() as session:
        # Get Byetta
        result = await session.execute(
            select(DrugLabel).where(DrugLabel.name == "Byetta")
        )
        drug = result.scalar_one_or_none()
        
        if not drug:
            print("❌ Byetta not found in database!")
            return
        
        print(f"✅ Drug: {drug.name}")
        print(f"   ID: {drug.id}")
        print(f"   Manufacturer: {drug.manufacturer}")
        print(f"   Version: {drug.version}")
        
        # Get sections
        sections_result = await session.execute(
            select(DrugSection)
            .where(DrugSection.drug_label_id == drug.id)
            .order_by(DrugSection.section_number)
        )
        sections = sections_result.scalars().all()
        
        print(f"\n✅ Sections: {len(sections)} total")
        
        # Group by level
        by_level = {}
        for section in sections:
            level = section.level
            if level not in by_level:
                by_level[level] = []
            by_level[level].append(section)
        
        for level in sorted(by_level.keys()):
            print(f"   Level {level}: {len(by_level[level])} sections")
        
        # Show first 10 sections
        print(f"\n📋 First 10 sections:")
        print(f"{'Number':<12} {'Level':<6} {'Parent':<8} {'Title'}")
        print("-" * 80)
        
        for section in sections[:10]:
            parent = f"→ {section.parent_section_id}" if section.parent_section_id else "ROOT"
            print(f"{section.section_number:<12} {section.level:<6} {parent:<8} {section.title[:50]}")
        
        # Check hierarchy
        sections_with_parents = len([s for s in sections if s.parent_section_id is not None])
        print(f"\n✅ Hierarchy check:")
        print(f"   Sections with parents: {sections_with_parents}")
        print(f"   Root sections: {len(sections) - sections_with_parents}")


if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════════╗
║           PARSE BYETTA WITH HIERARCHICAL PARSER                ║
║              Save to Database for Frontend View                ║
╚════════════════════════════════════════════════════════════════╝
    """)
    
    success = asyncio.run(parse_and_save_byetta())
    
    if success:
        asyncio.run(verify_data())
        
        print("\n" + "="*80)
        print("🎉 READY TO VIEW IN FRONTEND!")
        print("="*80)
        print("\nNext steps:")
        print("1. Start backend:  cd backend && python3 main.py")
        print("2. Start frontend: cd frontend && npm run dev")
        print("3. Open browser:   http://localhost:3000")
        print("4. Navigate to Byetta label to see hierarchical structure")
        print("\n" + "="*80 + "\n")
