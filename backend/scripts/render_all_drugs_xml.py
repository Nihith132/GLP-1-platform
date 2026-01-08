"""
Update ALL drugs with direct XML-to-HTML rendering
This bypasses parsing complexity and renders labels as complete documents
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from etl.xml_renderer import XMLRenderer
from models.db_session import AsyncSessionLocal
from models.database import DrugLabel, DrugSection
import asyncio
from sqlalchemy import select, delete


async def update_all_with_xml_rendering():
    """
    Update all drugs to use direct XML rendering
    This creates a single "Full Label" section per drug
    """
    
    # Get all ZIP files
    data_dir = Path(__file__).parent.parent.parent / 'data' / 'raw'
    zip_files = sorted(data_dir.glob('*.zip'))
    
    print(f"\n{'='*80}")
    print(f"📄 DIRECT XML RENDERING - ALL DRUGS")
    print(f"{'='*80}")
    print(f"Found {len(zip_files)} drug ZIP files")
    print(f"This will render each label as a complete, styled document\n")
    
    renderer = XMLRenderer()
    success_count = 0
    failed_count = 0
    
    async with AsyncSessionLocal() as session:
        for idx, zip_path in enumerate(zip_files, 1):
            try:
                print(f"\n[{idx}/{len(zip_files)}] 📦 Processing: {zip_path.name}")
                print("-" * 80)
                
                # Render XML to HTML
                result = renderer.render_xml_to_html(str(zip_path))
                
                if not result:
                    print(f"   ❌ Failed to render XML")
                    failed_count += 1
                    continue
                
                metadata = result['metadata']
                html_content = result['html']
                
                set_id = metadata.get('set_id', '')
                drug_name = metadata.get('name', 'Unknown')
                
                print(f"   📋 SET ID: {set_id}")
                print(f"   💊 Drug: {drug_name}")
                print(f"   📏 HTML Size: {len(html_content):,} characters")
                
                # Find drug in database by SET ID
                stmt = select(DrugLabel).where(DrugLabel.set_id == set_id)
                drug_result = await session.execute(stmt)
                drug = drug_result.scalar_one_or_none()
                
                if not drug:
                    print(f"   ⚠️  Drug not found in database")
                    failed_count += 1
                    continue
                
                print(f"   🆔 Drug ID: {drug.id}")
                
                # Delete existing sections
                delete_stmt = delete(DrugSection).where(DrugSection.drug_label_id == drug.id)
                deleted = await session.execute(delete_stmt)
                print(f"   🗑️  Cleared {deleted.rowcount} old sections")
                
                # Create single section with full rendered HTML
                new_section = DrugSection(
                    drug_label_id=drug.id,
                    loinc_code='FULL-LABEL',
                    title='Complete Drug Label',
                    order=1,
                    content=html_content
                )
                session.add(new_section)
                
                # Commit changes
                await session.commit()
                success_count += 1
                print(f"   ✅ UPDATED WITH XML-RENDERED HTML!")
                
            except Exception as e:
                print(f"\n   ❌ ERROR: {str(e)}")
                await session.rollback()
                failed_count += 1
                import traceback
                traceback.print_exc()
                continue
    
    # Summary
    print(f"\n{'='*80}")
    print(f"📊 RENDERING COMPLETE!")
    print(f"{'='*80}")
    print(f"✅ Successfully rendered: {success_count}/{len(zip_files)} drugs")
    print(f"❌ Failed: {failed_count}/{len(zip_files)} drugs")
    print(f"{'='*80}\n")
    
    if success_count == len(zip_files):
        print("🎉 ALL DRUGS RENDERED AS COMPLETE DOCUMENTS!")
        print("📄 Each label is now a professional, styled document")
        print("🔍 Consistent rendering across all drugs")
        print(f"\n🌐 View at: http://localhost:3000")
    else:
        print("⚠️  Some drugs failed to render. Check errors above.")


if __name__ == "__main__":
    asyncio.run(update_all_with_xml_rendering())
