"""
Test script for XML parser
Tests parsing on one FDA label file
"""

import sys
from pathlib import Path
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.etl.parser import parse_fda_label


def test_parser():
    """Test the parser on the first available FDA file"""
    
    print("=" * 60)
    print("🧪 FDA XML PARSER TEST")
    print("=" * 60)
    print()
    
    # Find first zip file in data/raw
    data_dir = project_root / "data" / "raw"
    zip_files = list(data_dir.glob("*.zip"))
    
    if not zip_files:
        print("❌ No FDA label files found in data/raw/")
        print("Please ensure files are downloaded and in the correct location")
        return False
    
    test_file = zip_files[0]
    print(f"📄 Testing with: {test_file.name}")
    print()
    
    # Parse the file
    print("Parsing XML...")
    result = parse_fda_label(str(test_file))
    
    if not result:
        print("❌ Failed to parse file")
        return False
    
    print("✅ Successfully parsed!")
    print()
    
    # Display metadata
    print("=" * 60)
    print("📋 EXTRACTED METADATA")
    print("=" * 60)
    metadata = result.get('metadata', {})
    for key, value in metadata.items():
        print(f"  {key}: {value}")
    print()
    
    # Display sections
    print("=" * 60)
    print("📑 EXTRACTED SECTIONS")
    print("=" * 60)
    sections = result.get('sections', [])
    print(f"Total sections: {len(sections)}")
    print()
    
    for i, section in enumerate(sections, 1):
        content_preview = section['content'][:100] + "..." if len(section['content']) > 100 else section['content']
        print(f"{i}. {section['title']} (LOINC: {section['loinc_code']})")
        print(f"   Content length: {len(section['content'])} chars")
        print(f"   Preview: {content_preview}")
        print()
    
    # Show full content of first section as example
    if sections:
        print("=" * 60)
        print(f"📖 FULL CONTENT EXAMPLE: {sections[0]['title']}")
        print("=" * 60)
        print(sections[0]['content'][:500])
        print("...")
        print()
    
    print("=" * 60)
    print("🎉 PARSER TEST SUCCESSFUL!")
    print("=" * 60)
    print()
    print("Next step: Build NER service to extract entities from text")
    
    return True


if __name__ == "__main__":
    try:
        success = test_parser()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
