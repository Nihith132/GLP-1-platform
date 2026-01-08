"""
Parse Qsymia with hierarchical parser and save to database
Test the improved parser before running all 19 drugs
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


async def parse_and_save_qsymia():
    """Parse Qsymia and save to database"""
    
    print("\n" + "="*80)
    print("📦 PARSING QSYMIA WITH HIERARCHICAL PARSER")
    print("="*80 + "\n")
    
    # Parse Qsymia
    data_dir = Path(__file__).parent.parent.parent / 'data' / 'raw'
    qsymia_zip = data_dir / '20250910_40dd5602-53da-45ac-bb4b-15789aba40f9.zip'
    
    if not qsymia_zip.exists():
        print(f"❌ File not found: {qsymia_zip}")
        return False
    
    parser = HierarchicalParser()
    print(f"📁 Parsing: {qsymia_zip.name}")
    result = parser.parse_zip_file(str(qsymia_zip))
    
    if not result:
        print("❌ Parsing failed!")
        return False
    
    metadata = result['metadata']
    sections = result['sections']
    
    print(f"✅ Parsed successfully!")
    print(f"   - {len(sections)} total sections")
    print(f"   - {len([s for s in sections if s['level'] == 1])} main sections")
    print(f"   - {len([s for s in sections if s['level'] > 1])} subsections")
    
    # Check for duplicates
    from collections import Counter
    title_counts = Counter(s['title'] for s in sections)
    duplicates = {title: count for title, count in title_counts.items() if count > 1}
    if duplicates:
        print(f"   - {len(duplicates)} duplicate titles found:")
        for title, count in sorted(duplicates.items(), key=lambda x: -x[1])[:5]:
            print(f"     • {count}x: {title}")
    else:
        print(f"   - ✅ No duplicate titles!")
    
    # Save to database
    print(f"\n💾 Saving to database...")
    
    async with AsyncSessionLocal() as session:
        try:
            # Check if Qsymia already exists
            existing = await session.execute(
                select(DrugLabel).where(DrugLabel.name == "Qsymia")
            )
            existing_drug = existing.scalar_one_or_none()
            
            if existing_drug:
                print(f"   Found existing Qsymia (ID: {existing_drug.id})")
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
                existing_drug.source_file = qsymia_zip.name
                
                drug = existing_drug
                print(f"   Updated drug metadata")
            else:
                # Create new drug label
                drug = DrugLabel(
                    name="Qsymia",
                    generic_name=metadata.get('generic_name', 'phentermine and topiramate'),
                    manufacturer=metadata['manufacturer'],
                    set_id=metadata['set_id'],
                    version=metadata['version'],
                    is_current_version=True,
                    status="active",
                    last_updated=datetime.utcnow(),
                    source_file=qsymia_zip.name
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
            
            parent_count = 0
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
                        parent_count += 1
            
            # Commit all changes
            await session.commit()
            
            print(f"\n✅ Successfully saved Qsymia to database!")
            print(f"   Drug ID: {drug.id}")
            print(f"   Sections saved: {len(sections)}")
            print(f"   Parent-child relationships: {parent_count}")
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
    print("🔍 VERIFYING QSYMIA DATA")
    print("="*80 + "\n")
    
    async with AsyncSessionLocal() as session:
        # Get Qsymia
        result = await session.execute(
            select(DrugLabel).where(DrugLabel.name == "Qsymia")
        )
        drug = result.scalar_one_or_none()
        
        if not drug:
            print("❌ Qsymia not found in database!")
            return
        
        print(f"✅ Drug: {drug.name}")
        print(f"   ID: {drug.id}")
        print(f"   Manufacturer: {drug.manufacturer}")
        print(f"   Version: {drug.version}")
        
        # Get sections
        sections_result = await session.execute(
            select(DrugSection)
            .where(DrugSection.drug_label_id == drug.id)
        )
        sections = list(sections_result.scalars().all())
        
        print(f"\n📊 Sections breakdown:")
        print(f"   Total: {len(sections)}")
        
        # Count by level
        from collections import Counter
        level_counts = Counter(s.level for s in sections)
        for level in sorted(level_counts.keys()):
            print(f"   Level {level}: {level_counts[level]}")
        
        # Check for duplicates
        title_counts = Counter(s.title for s in sections)
        duplicates = {title: count for title, count in title_counts.items() if count > 1}
        if duplicates:
            print(f"\n⚠️  Duplicate titles: {len(duplicates)}")
            for title, count in sorted(duplicates.items(), key=lambda x: -x[1])[:5]:
                print(f"   • {count}x: {title}")
        else:
            print(f"\n✅ No duplicate titles!")
        
        # Show first 10 sections
        print(f"\n📝 First 10 sections:")
        print("="*80)
        for i, s in enumerate(sections[:10], 1):
            indent = '  ' * (s.level - 1)
            print(f"{i:2d}. {indent}{s.section_number:10s} | L{s.level} | {s.title[:50]}")


if __name__ == "__main__":
    success = asyncio.run(parse_and_save_qsymia())
    
    if success:
        asyncio.run(verify_data())
        print(f"\n" + "="*80)
        print("✅ Qsymia parsing complete!")
        print("   View at: http://localhost:3000/analysis/8")
        print("="*80 + "\n")
    else:
        print(f"\n❌ Qsymia parsing failed!")
        sys.exit(1)
