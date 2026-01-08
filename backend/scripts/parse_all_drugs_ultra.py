"""
Parse ALL 19 drugs with Ultra-Refined Parser
Ensures consistent parsing across all drug labels for comparison
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from etl.parser_ultra_refined import UltraRefinedParser
from models.db_session import AsyncSessionLocal
from models.database import DrugLabel, DrugSection
import asyncio
from sqlalchemy import select, delete


async def parse_all_drugs():
    """Parse all 19 drugs with ultra-refined parser for consistent comparison"""
    
    # Get all ZIP files
    data_dir = Path(__file__).parent.parent.parent / 'data' / 'raw'
    zip_files = sorted(data_dir.glob('*.zip'))
    
    print(f"\n{'='*80}")
    print(f"🔍 ULTRA-REFINED PARSING - ALL DRUGS")
    print(f"{'='*80}")
    print(f"Found {len(zip_files)} drug ZIP files\n")
    
    parser = UltraRefinedParser()
    success_count = 0
    failed_count = 0
    
    async with AsyncSessionLocal() as session:
        for idx, zip_path in enumerate(zip_files, 1):
            try:
                print(f"\n[{idx}/{len(zip_files)}] 📦 Processing: {zip_path.name}")
                print("-" * 80)
                
                # Parse with ultra-refined structure
                result = parser.parse_zip_file(str(zip_path))
                
                if not result:
                    print(f"   ❌ Failed to parse ZIP file")
                    failed_count += 1
                    continue
                
                metadata = result['metadata']
                sections = result['sections']
                
                set_id = metadata.get('set_id')
                drug_name = metadata.get('name', 'Unknown')
                
                print(f"   📋 SET ID: {set_id}")
                print(f"   💊 Drug: {drug_name}")
                print(f"   📑 Sections: {len(sections)}")
                
                # Find drug in database by SET ID
                stmt = select(DrugLabel).where(DrugLabel.set_id == set_id)
                drug_result = await session.execute(stmt)
                drug = drug_result.scalar_one_or_none()
                
                if not drug:
                    print(f"   ⚠️  Drug not found in database")
                    failed_count += 1
                    continue
                
                print(f"   🆔 Drug ID: {drug.id}")
                
                # Delete existing sections for this drug
                delete_stmt = delete(DrugSection).where(DrugSection.drug_label_id == drug.id)
                deleted = await session.execute(delete_stmt)
                print(f"   🗑️  Cleared {deleted.rowcount} old sections")
                
                # Insert new ultra-refined sections
                print(f"\n   📝 Inserting Ultra-Refined Sections:")
                for section in sections:
                    section_num = section['section_number']
                    
                    new_section = DrugSection(
                        drug_label_id=drug.id,
                        section_code=section['code'],
                        section_title=section['title'],
                        section_number=section_num,
                        content_text=section['content'][:10000],  # Truncate text preview
                        content_html=section['html'],  # Full HTML with semantic markup
                        importance_level=section.get('importance', 'medium'),
                        has_table='<table' in section['html'].lower(),
                        has_list='<ul' in section['html'].lower() or '<ol' in section['html'].lower(),
                        word_count=len(section['content'].split())
                    )
                    session.add(new_section)
                    
                    # Show importance indicator
                    importance_icon = {
                        'critical': '🔴',
                        'high': '🟠', 
                        'medium': '🟡',
                        'low': '⚪'
                    }.get(section.get('importance', 'medium'), '⚪')
                    
                    print(f"      {importance_icon} [{section_num}] {section['title']}")
                
                # Commit changes
                await session.commit()
                success_count += 1
                print(f"\n   ✅ UPDATED WITH ULTRA-REFINED HTML!")
                
            except Exception as e:
                print(f"\n   ❌ ERROR: {str(e)}")
                await session.rollback()
                failed_count += 1
                import traceback
                traceback.print_exc()
                continue
    
    # Summary
    print(f"\n{'='*80}")
    print(f"📊 PARSING COMPLETE!")
    print(f"{'='*80}")
    print(f"✅ Successfully parsed: {success_count}/{len(zip_files)} drugs")
    print(f"❌ Failed: {failed_count}/{len(zip_files)} drugs")
    print(f"{'='*80}\n")
    
    if success_count == len(zip_files):
        print("🎉 ALL DRUGS PARSED WITH CONSISTENT ULTRA-REFINED STRUCTURE!")
        print("🔍 Ready for analysis and comparison!")
        print(f"\n🌐 View any drug at: http://localhost:3000/analysis/[drug_id]")
    else:
        print("⚠️  Some drugs failed to parse. Check errors above.")


if __name__ == "__main__":
    asyncio.run(parse_all_drugs())
