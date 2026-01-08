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


async def parse_one_drug_test():
    """Test parsing ONE drug first before doing all"""
    
    # Get first ZIP file to test
    data_dir = Path(__file__).parent.parent.parent / 'data' / 'raw'
    zip_files = sorted(data_dir.glob('*.zip'))
    
    if not zip_files:
        print("❌ No ZIP files found!")
        return False
    
    test_zip = zip_files[0]  # Test with first drug
    
    print(f"\n{'='*80}")
    print(f"🧪 TESTING ULTRA-REFINED PARSER - ONE DRUG")
    print(f"{'='*80}")
    print(f"📦 Test file: {test_zip.name}\n")
    
    parser = UltraRefinedParser()
    
    try:
        # Parse with ultra-refined structure
        result = parser.parse_zip_file(str(test_zip))
        
        if not result:
            print(f"❌ Failed to parse ZIP file")
            return False
        
        metadata = result['metadata']
        sections = result['sections']
        
        set_id = metadata['set_id']
        drug_name = metadata['name']
        
        print(f"✅ PARSED SUCCESSFULLY!")
        print(f"   📋 SET ID: {set_id}")
        print(f"   💊 Drug: {drug_name}")
        print(f"   📑 Sections: {len(sections)}")
        print(f"   📋 Metadata: {list(metadata.keys())}")
        
        # Show section structure
        print(f"\n📝 Section Structure:")
        for section in sections[:5]:  # Show first 5
            importance_icon = {
                'critical': '🔴',
                'high': '🟠',
                'medium': '🟡',
                'low': '⚪'
            }.get(section.get('importance', 'medium'), '⚪')
            
            print(f"   {importance_icon} [{section['section_number']}] {section['title']}")
            print(f"      LOINC: {section['loinc_code']}")
            print(f"      Importance: {section.get('importance', 'medium')}")
        
        # Now update database
        print(f"\n🔄 Updating Database...")
        async with AsyncSessionLocal() as session:
            # Find drug in database by SET ID
            stmt = select(DrugLabel).where(DrugLabel.set_id == set_id)
            drug_result = await session.execute(stmt)
            drug = drug_result.scalar_one_or_none()
            
            if not drug:
                print(f"   ⚠️  Drug not found in database with SET ID: {set_id}")
                return False
            
            print(f"   🆔 Drug ID: {drug.id}")
            
            # Delete existing sections for this drug
            delete_stmt = delete(DrugSection).where(DrugSection.drug_label_id == drug.id)
            deleted = await session.execute(delete_stmt)
            print(f"   🗑️  Cleared {deleted.rowcount} old sections")
            
            # Insert new ultra-refined sections
            print(f"\n   📝 Inserting Ultra-Refined Sections:")
            for section in sections:
                new_section = DrugSection(
                    drug_label_id=drug.id,
                    loinc_code=section['loinc_code'],
                    title=section['title'],
                    order=int(section['section_number']) if isinstance(section['section_number'], str) else section['section_number'],
                    content=section['content']  # Full HTML with semantic markup
                )
                session.add(new_section)
                
                # Show importance indicator
                importance_icon = {
                    'critical': '🔴',
                    'high': '🟠',
                    'medium': '🟡',
                    'low': '⚪'
                }.get(section.get('importance', 'medium'), '⚪')
                
                print(f"      {importance_icon} [{section['section_number']}] {section['title']}")
            
            # Commit changes
            await session.commit()
            print(f"\n   ✅ DATABASE UPDATED WITH ULTRA-REFINED HTML!")
            print(f"\n🌐 View at: http://localhost:3000/analysis/{drug.id}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


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
                
                set_id = metadata['set_id']
                drug_name = metadata['name']
                
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
                    new_section = DrugSection(
                        drug_label_id=drug.id,
                        loinc_code=section['loinc_code'],
                        title=section['title'],
                        order=int(section['section_number']) if isinstance(section['section_number'], str) else section['section_number'],
                        content=section['content']  # Full HTML with semantic markup
                    )
                    session.add(new_section)
                    
                    # Show importance indicator
                    importance_icon = {
                        'critical': '🔴',
                        'high': '🟠',
                        'medium': '🟡',
                        'low': '⚪'
                    }.get(section.get('importance', 'medium'), '⚪')
                    
                    print(f"      {importance_icon} [{section['section_number']}] {section['title']}")
                
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
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        # Parse all drugs
        asyncio.run(parse_all_drugs())
    else:
        # Test with one drug first
        success = asyncio.run(parse_one_drug_test())
        if success:
            print(f"\n✅ Test successful! Run with --all to parse all drugs:")
            print(f"   python scripts/parse_all_drugs_ultra_fixed.py --all")
        else:
            print(f"\n❌ Test failed. Fix errors before parsing all drugs.")
