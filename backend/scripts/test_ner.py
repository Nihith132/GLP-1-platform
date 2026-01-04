"""
Test script for NER service
Tests entity extraction on sample text
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.etl.ner import get_ner_service
from backend.etl.parser import parse_fda_label


def test_ner():
    """Test NER on parsed FDA label"""
    
    print("=" * 60)
    print("🧪 MEDICAL NER TEST")
    print("=" * 60)
    print()
    
    # Get NER service
    print("Initializing NER service...")
    ner_service = get_ner_service()
    print("✅ NER service ready")
    print()
    
    # Find first zip file
    data_dir = project_root / "data" / "raw"
    zip_files = list(data_dir.glob("*.zip"))
    
    if not zip_files:
        print("❌ No FDA label files found")
        return False
    
    # Parse the file
    test_file = zip_files[0]
    print(f"📄 Testing with: {test_file.name}")
    result = parse_fda_label(str(test_file))
    
    if not result:
        print("❌ Failed to parse file")
        return False
    
    print()
    
    # Test NER on first few sections
    sections = result['sections'][:5]  # First 5 sections
    
    all_entities = []
    
    for section in sections:
        print("=" * 60)
        print(f"📑 Section: {section['title']}")
        print(f"   LOINC: {section['loinc_code']}")
        print("=" * 60)
        print()
        
        # Extract entities
        entities = ner_service.extract_entities(
            section['content'], 
            section_type=section['loinc_code']
        )
        
        if entities:
            print(f"Found {len(entities)} entities:")
            print()
            
            # Group by type
            by_type = {}
            for entity in entities:
                label = entity['label']
                if label not in by_type:
                    by_type[label] = []
                by_type[label].append(entity['text'])
            
            # Display grouped
            for label, texts in by_type.items():
                unique_texts = list(set(texts))[:5]  # Show first 5 unique
                print(f"  {label}:")
                for text in unique_texts:
                    print(f"    • {text}")
                if len(unique_texts) < len(set(texts)):
                    print(f"    ... and {len(set(texts)) - len(unique_texts)} more")
                print()
        else:
            print("  No entities found in this section")
            print()
        
        all_entities.extend(entities)
    
    # Summary
    print("=" * 60)
    print("📊 OVERALL SUMMARY")
    print("=" * 60)
    
    summary = ner_service.summarize_entities(all_entities)
    
    print(f"\nTotal entities extracted: {len(all_entities)}")
    print("\nBreakdown by type:")
    for label, count in sorted(summary.items()):
        print(f"  {label}: {count}")
    
    print()
    print("=" * 60)
    print("🎉 NER TEST SUCCESSFUL!")
    print("=" * 60)
    print()
    print("Next step: Build vector embedding service")
    
    return True


if __name__ == "__main__":
    try:
        success = test_ner()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
