"""
Test Hierarchical Parser on Byetta
Validates:
- Section hierarchy (numbering, parent-child)
- Clean titles (no "SPL UNCLASSIFIED")
- Table handling (human-readable format)
- Content quality
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from etl.parser_hierarchical import HierarchicalParser
import json


def test_byetta():
    """Test parser on Byetta label"""
    
    print("\n" + "="*80)
    print("🧪 TESTING HIERARCHICAL PARSER ON BYETTA")
    print("="*80 + "\n")
    
    # Path to Byetta ZIP file
    data_dir = Path(__file__).parent.parent.parent / 'data' / 'raw'
    byetta_zip = data_dir / '20250906_53d03c03-ebf7-418d-88a8-533eabd2ee4f.zip'
    
    if not byetta_zip.exists():
        print(f"❌ Byetta ZIP file not found: {byetta_zip}")
        return
    
    print(f"📁 Parsing: {byetta_zip.name}\n")
    
    # Parse
    parser = HierarchicalParser()
    result = parser.parse_zip_file(str(byetta_zip))
    
    if not result:
        print("❌ Parsing failed!")
        return
    
    # Display metadata
    print("📋 METADATA:")
    print("-" * 80)
    metadata = result['metadata']
    for key, value in metadata.items():
        print(f"  {key:20}: {value}")
    
    # Analyze sections
    sections = result['sections']
    
    print(f"\n📚 SECTIONS: {len(sections)} total")
    print("=" * 80)
    
    # Group by level
    by_level = {}
    for section in sections:
        level = section['level']
        if level not in by_level:
            by_level[level] = []
        by_level[level].append(section)
    
    print(f"\nSection Distribution:")
    for level in sorted(by_level.keys()):
        print(f"  Level {level}: {len(by_level[level])} sections")
    
    # Display section structure
    print(f"\n{'Number':<10} {'Level':<6} {'LOINC':<12} {'Title'}")
    print("-" * 90)
    
    for section in sections:
        num = section['section_number']
        level = section['level']
        loinc = section.get('loinc_code', 'N/A') or 'N/A'
        title = section['title'][:60]
        
        indent = "  " * (level - 1)
        print(f"{num:<10} {level:<6} {loinc:<12} {indent}{title}")
    
    # Quality checks
    print("\n" + "="*80)
    print("✅ QUALITY CHECKS")
    print("="*80)
    
    issues = {
        'unclassified': 0,
        'missing_title': 0,
        'empty_content': 0,
        'missing_loinc': 0
    }
    
    for section in sections:
        if 'UNCLASSIFIED' in section['title'].upper():
            issues['unclassified'] += 1
        if not section['title'] or section['title'].strip() == '':
            issues['missing_title'] += 1
        if not section.get('content') or len(section['content'].strip()) < 20:
            issues['empty_content'] += 1
        if section['level'] == 1 and not section.get('loinc_code'):
            issues['missing_loinc'] += 1
    
    print(f"\n✓ Clean titles: {len(sections) - issues['unclassified']} / {len(sections)}")
    print(f"✗ 'SPL UNCLASSIFIED': {issues['unclassified']}")
    print(f"✓ All titled: {len(sections) - issues['missing_title']} / {len(sections)}")
    print(f"✗ Missing titles: {issues['missing_title']}")
    print(f"✓ Good content: {len(sections) - issues['empty_content']} / {len(sections)}")
    print(f"✗ Empty content: {issues['empty_content']}")
    print(f"✗ Main sections without LOINC: {issues['missing_loinc']}")
    
    # Show sample content from first main section
    main_sections = [s for s in sections if s['level'] == 1]
    if main_sections:
        sample = main_sections[0]
        print(f"\n" + "="*80)
        print(f"📄 SAMPLE CONTENT: {sample['title']}")
        print("="*80)
        print(f"Section Number: {sample['section_number']}")
        print(f"LOINC Code: {sample.get('loinc_code', 'N/A')}")
        print(f"Level: {sample['level']}")
        print(f"\nContent Preview (first 500 chars):")
        print("-" * 80)
        content = sample.get('content', '')
        print(content[:500] + "..." if len(content) > 500 else content)
        
        # Show HTML preview too
        html = sample.get('content_html', '')
        if html:
            print(f"\nHTML Preview (first 300 chars):")
            print("-" * 80)
            print(html[:300] + "..." if len(html) > 300 else html)
    
    # Check for tables
    print(f"\n" + "="*80)
    print("📊 TABLE ANALYSIS")
    print("="*80)
    
    sections_with_tables = 0
    for section in sections:
        content = section.get('content', '')
        if '|' in content or 'Table' in content:
            sections_with_tables += 1
    
    print(f"\nSections with table data: {sections_with_tables}")
    
    # Show table example if exists
    for section in sections:
        content = section.get('content', '')
        if '|' in content and len(content.split('\n')) > 3:
            print(f"\n📊 Table Example from: {section['title']}")
            print("-" * 80)
            # Show first 10 lines of table
            table_lines = content.split('\n')[:10]
            for line in table_lines:
                print(line)
            if len(content.split('\n')) > 10:
                print("...")
            break
    
    # Summary
    print(f"\n" + "="*80)
    print("📊 SUMMARY")
    print("="*80)
    print(f"✅ Total sections parsed: {len(sections)}")
    print(f"✅ Main sections (Level 1): {len([s for s in sections if s['level'] == 1])}")
    print(f"✅ Subsections (Level 2+): {len([s for s in sections if s['level'] > 1])}")
    print(f"✅ Average content length: {sum(len(s.get('content', '')) for s in sections) // len(sections)} chars")
    print(f"✅ Sections with LOINC codes: {len([s for s in sections if s.get('loinc_code')])}")
    
    if issues['unclassified'] == 0 and issues['missing_title'] == 0:
        print(f"\n🎉 PERFECT! No quality issues found!")
    else:
        print(f"\n⚠️  Found {issues['unclassified'] + issues['missing_title']} quality issues")
    
    print("\n" + "="*80 + "\n")
    
    # Return for potential further analysis
    return result


if __name__ == "__main__":
    result = test_byetta()
    
    if result:
        print("✅ Test completed successfully!")
        print("\nNext steps:")
        print("1. Review the section structure above")
        print("2. Check if hierarchy looks correct")
        print("3. Verify table formatting is readable")
        print("4. If good, proceed to parse all drugs")
    else:
        print("❌ Test failed!")
