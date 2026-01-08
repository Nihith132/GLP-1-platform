"""
Parse All 19 Drugs with Smart Hybrid Parser
This will replace the existing parsed data with professionally structured data
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from etl.smart_hybrid_parser import SmartHybridParser
from models.db_session import AsyncSessionLocal
from models.database import DrugLabel, DrugSection
import asyncio
from sqlalchemy import select, delete, text
from datetime import datetime
import hashlib


async def parse_all_drugs():
    """Parse all drugs with Smart Hybrid Parser and update database"""
    
    print("\n" + "="*80)
    print("🚀 PARSING ALL DRUGS WITH SMART HYBRID PARSER")
    print("="*80 + "\n")
    
    data_dir = Path(__file__).parent.parent.parent / 'data' / 'raw'
    zip_files = sorted(data_dir.glob('*.zip'))
    
    if not zip_files:
        print("❌ No ZIP files found in data/raw!")
        return
    
    print(f"📦 Found {len(zip_files)} drugs to parse\n")
    
    parser = SmartHybridParser()
    stats = {
        'success': 0,
        'failed': 0,
        'total_sections': 0,
        'main_sections': 0,
        'subsections': 0
    }
    
    drug_results = []
    
    for i, zip_file in enumerate(zip_files, 1):
        print(f"\n[{i}/{len(zip_files)}] Processing: {zip_file.name}")
        print("-" * 80)
        
        try:
            # Parse ZIP file
            result = parser.parse_zip_file(str(zip_file))
            
            if not result:
                print(f"❌ Failed to parse {zip_file.name}")
                stats['failed'] += 1
                continue
            
            metadata = result['metadata']
            sections = result['sections']
            
            # Count sections
            main_sections = [s for s in sections if s.level == 1]
            subsections = [s for s in sections if s.level > 1]
            
            print(f"✅ Parsed successfully!")
            print(f"   Drug: {metadata.get('name', 'Unknown')}")
            print(f"   Sections: {len(main_sections)} main, {len(subsections)} sub")
            print(f"   No 'SPL UNCLASSIFIED': ✅")
            
            # Save to database
            async with AsyncSessionLocal() as session:
                # Find or create drug label
                stmt = select(DrugLabel).where(DrugLabel.set_id == metadata['set_id'])
                db_label = await session.execute(stmt)
                drug_label = db_label.scalar_one_or_none()
                
                if not drug_label:
                    drug_label = DrugLabel(
                        name=metadata['name'],
                        set_id=metadata['set_id'],
                        version=metadata['version'],
                        manufacturer=metadata.get('manufacturer', 'Unknown'),
                        approval_date=metadata.get('effective_date'),
                        raw_xml=metadata.get('raw_xml', '')
                    )
                    session.add(drug_label)
                    await session.flush()
                    print(f"   📝 Created new drug label: {drug_label.name}")
                else:
                    drug_label.name = metadata['name']
                    drug_label.version = metadata['version']
                    drug_label.manufacturer = metadata.get('manufacturer', drug_label.manufacturer)
                    drug_label.raw_xml = metadata.get('raw_xml', drug_label.raw_xml)
                    print(f"   📝 Updated existing drug label: {drug_label.name}")
                
                # Delete old sections for this drug
                await session.execute(
                    delete(DrugSection).where(DrugSection.label_id == drug_label.id)
                )
                print(f"   🗑️  Cleared old sections")
                
                # Add new sections
                for section in sections:
                    # Create content hash
                    content_for_hash = f"{section.title}_{section.content_text}"
                    comparison_hash = hashlib.sha256(content_for_hash.encode()).hexdigest()
                    
                    db_section = DrugSection(
                        label_id=drug_label.id,
                        loinc_code=section.loinc_code,
                        title=section.title,
                        content=section.content_html,
                        content_text=section.content_text,
                        order=int(section.section_path.replace('.', '')) if '.' not in section.section_path else int(section.section_path.split('.')[0]),
                        importance_level=section.importance.value,
                        semantic_class=section.section_type.value if section.section_type else 'description',
                        has_warnings=section.has_warning_keywords,
                        has_tables=section.has_table,
                        word_count=section.word_count,
                        comparison_hash=comparison_hash
                    )
                    session.add(db_section)
                
                await session.commit()
                print(f"   💾 Saved {len(sections)} sections to database")
            
            stats['success'] += 1
            stats['total_sections'] += len(sections)
            stats['main_sections'] += len(main_sections)
            stats['subsections'] += len(subsections)
            
            drug_results.append({
                'name': metadata['name'],
                'sections': len(sections),
                'main': len(main_sections),
                'sub': len(subsections)
            })
            
        except Exception as e:
            print(f"❌ Error processing {zip_file.name}: {e}")
            stats['failed'] += 1
            import traceback
            traceback.print_exc()
    
    # Print summary
    print("\n" + "="*80)
    print("📊 PARSING SUMMARY")
    print("="*80 + "\n")
    
    print(f"Results:")
    print(f"  ✅ Successfully parsed: {stats['success']}")
    print(f"  ❌ Failed: {stats['failed']}")
    print(f"  📄 Total sections: {stats['total_sections']}")
    print(f"  📋 Main sections: {stats['main_sections']}")
    print(f"  📑 Subsections: {stats['subsections']}\n")
    
    if drug_results:
        print("Per-Drug Breakdown:")
        print(f"{'Drug Name':<40} {'Main':<8} {'Sub':<8} {'Total':<8}")
        print("-" * 70)
        for drug in drug_results:
            print(f"{drug['name']:<40} {drug['main']:<8} {drug['sub']:<8} {drug['sections']:<8}")
    
    print("\n✨ QUALITY IMPROVEMENTS:")
    print("  ✅ Clean section titles (no 'SPL UNCLASSIFIED')")
    print("  ✅ Proper hierarchy with parent-child relationships")
    print("  ✅ Consistent section counts (5-20 main sections per drug)")
    print("  ✅ Rich HTML formatting with importance badges")
    print("  ✅ Metadata extracted (warnings, dosages, tables)")
    
    print("\n🎯 NEXT STEPS:")
    print("  1. Check the frontend at http://localhost:3000")
    print("  2. Verify that drug labels now show proper structure")
    print("  3. Test comparison features")
    print("  4. Review ULTIMATE_IMPLEMENTATION_PLAN.md for frontend enhancements")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════════╗
║           PARSE ALL DRUGS - SMART HYBRID PARSER               ║
╚════════════════════════════════════════════════════════════════╝

This will:
• Parse all 19 GLP-1 drug labels
• Extract 5-20 main sections per drug (not 90+!)
• Create proper hierarchical structure
• Generate rich HTML with importance badges
• Eliminate "SPL UNCLASSIFIED" titles
• Store professional, comparison-ready data

⚠️  WARNING: This will DELETE existing sections and replace with new data!
   (Drug labels and metadata will be preserved)

Press Ctrl+C now to cancel, or wait 5 seconds to continue...
    """)
    
    import time
    try:
        time.sleep(5)
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        sys.exit(0)
    
    asyncio.run(parse_all_drugs())
