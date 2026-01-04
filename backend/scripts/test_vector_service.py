"""
Test script for Vector Embedding Service
Tests both label-level and section-level embeddings
"""

import sys
from pathlib import Path
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.etl.vector_service import get_vector_service
from backend.etl.parser import parse_fda_label


def test_vector_service():
    """Test vector embedding generation"""
    
    print("=" * 60)
    print("🧪 VECTOR EMBEDDING SERVICE TEST")
    print("=" * 60)
    print()
    
    # Initialize service
    print("Initializing vector service...")
    vector_service = get_vector_service()
    print(f"✅ Vector service ready (dimensions: {vector_service.dimensions})")
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
    
    metadata = result['metadata']
    sections = result['sections']
    
    print()
    print("=" * 60)
    print("TEST 1: Label-Level Embedding (for dashboard search)")
    print("=" * 60)
    print()
    
    # Get indications section for summary
    indications_section = next(
        (s for s in sections if s['loinc_code'] == '34067-9'), 
        None
    )
    
    # Create drug data for label embedding
    drug_data = {
        'name': metadata.get('name'),
        'generic_name': metadata.get('generic_name'),
        'manufacturer': metadata.get('manufacturer'),
        'indications': indications_section['content'][:500] if indications_section else None
    }
    
    print(f"Drug: {drug_data['name']}")
    print(f"Generic: {drug_data['generic_name']}")
    print(f"Manufacturer: {drug_data['manufacturer']}")
    print()
    
    # Generate label embedding
    label_embedding = vector_service.generate_label_embedding(drug_data)
    
    print(f"✅ Generated label embedding")
    print(f"   Shape: {label_embedding.shape}")
    print(f"   Dimensions: {len(label_embedding)}")
    print(f"   First 5 values: {label_embedding[:5]}")
    print()
    
    # Test similarity with different queries
    print("Testing search similarity:")
    queries = [
        "GLP-1 medication for type 2 diabetes",
        "weight loss drug",
        "heart medication",
        "cancer treatment"
    ]
    
    for query in queries:
        query_emb = vector_service.model.encode(query, normalize_embeddings=True)
        similarity = vector_service.compute_similarity(label_embedding, query_emb)
        print(f"  '{query}': {similarity:.3f}")
    
    print()
    print("=" * 60)
    print("TEST 2: Section-Level Embeddings (for RAG chatbot)")
    print("=" * 60)
    print()
    
    # Test with first 3 sections
    test_sections = sections[:3]
    
    for i, section in enumerate(test_sections, 1):
        print(f"Section {i}: {section['title']}")
        print(f"  LOINC: {section['loinc_code']}")
        print(f"  Text length: {len(section['content'])} chars")
        
        # Generate section embedding
        section_emb = vector_service.generate_section_embedding(
            section['content'],
            section['title']
        )
        
        print(f"  ✅ Embedding shape: {section_emb.shape}")
        print()
    
    print("=" * 60)
    print("TEST 3: Batch Embedding Generation")
    print("=" * 60)
    print()
    
    # Create text list from all sections
    section_texts = [
        f"{s['title']}: {s['content'][:500]}" 
        for s in sections[:5]
    ]
    
    print(f"Generating embeddings for {len(section_texts)} sections...")
    batch_embeddings = vector_service.generate_batch_embeddings(section_texts)
    
    print(f"✅ Generated {len(batch_embeddings)} embeddings")
    print(f"   Shape: {batch_embeddings.shape}")
    print()
    
    # Test similarity between sections
    print("Similarity between sections:")
    if len(batch_embeddings) >= 2:
        sim = vector_service.compute_similarity(
            batch_embeddings[0],
            batch_embeddings[1]
        )
        print(f"  Section 1 vs Section 2: {sim:.3f}")
    
    print()
    print("=" * 60)
    print("TEST 4: Search Query Matching")
    print("=" * 60)
    print()
    
    # Test queries against sections
    test_queries = [
        "What are the side effects?",
        "How do I take this medication?",
        "What is this drug used for?"
    ]
    
    for query in test_queries:
        print(f"Query: '{query}'")
        query_emb = vector_service.model.encode(query, normalize_embeddings=True)
        
        # Find most similar section
        best_match = None
        best_score = 0
        
        for i, section_emb in enumerate(batch_embeddings):
            sim = vector_service.compute_similarity(query_emb, section_emb)
            if sim > best_score:
                best_score = sim
                best_match = sections[i]['title']
        
        print(f"  → Best match: {best_match} (score: {best_score:.3f})")
        print()
    
    print("=" * 60)
    print("🎉 VECTOR SERVICE TEST SUCCESSFUL!")
    print("=" * 60)
    print()
    print("Summary:")
    print(f"  • Model: {vector_service.model_name}")
    print(f"  • Dimensions: {vector_service.dimensions}")
    print(f"  • Label embeddings: ✅ Working")
    print(f"  • Section embeddings: ✅ Working")
    print(f"  • Batch processing: ✅ Working")
    print(f"  • Semantic search: ✅ Working")
    print()
    print("Next step: Build ETL builder to orchestrate everything")
    
    return True


if __name__ == "__main__":
    try:
        success = test_vector_service()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
