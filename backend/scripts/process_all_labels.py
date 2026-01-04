"""
Process all FDA label files in batch
Runs the complete ETL pipeline on all files in data/raw/
"""

import sys
from pathlib import Path
import asyncio
import logging

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from backend.etl.etl_builder import ETLBuilder


async def process_all_fda_labels():
    """Process all FDA label files"""
    
    print("=" * 70)
    print("🚀 BATCH ETL PROCESSING - ALL FDA LABELS")
    print("=" * 70)
    print()
    
    # Find all zip files
    data_dir = project_root / "data" / "raw"
    zip_files = sorted(list(data_dir.glob("*.zip")))
    
    if not zip_files:
        print("❌ No FDA label files found in data/raw/")
        return False
    
    print(f"Found {len(zip_files)} FDA label files:")
    for i, file in enumerate(zip_files, 1):
        print(f"  {i}. {file.name}")
    print()
    
    # Initialize ETL builder
    print("Initializing ETL builder...")
    builder = ETLBuilder()
    print("✅ ETL builder ready")
    print()
    
    # Process all files
    print("=" * 70)
    print("STARTING BATCH PROCESSING")
    print("=" * 70)
    print()
    
    file_paths = [str(f) for f in zip_files]
    results = await builder.process_batch(file_paths)
    
    # Final summary
    print()
    print("=" * 70)
    print("📊 FINAL SUMMARY")
    print("=" * 70)
    print()
    print(f"✅ Successfully processed: {results['success']}/{len(zip_files)} files")
    print(f"❌ Failed: {results['failed']}/{len(zip_files)} files")
    print()
    
    if results['drug_label_ids']:
        print(f"Drug label IDs created: {results['drug_label_ids']}")
        print()
    
    print("=" * 70)
    print("🎉 BATCH PROCESSING COMPLETE!")
    print("=" * 70)
    print()
    
    if results['success'] > 0:
        print("Database now contains:")
        print(f"  • {results['success']} drug labels with embeddings")
        print(f"  • ~{results['success'] * 35} sections with NER entities")
        print(f"  • ~{results['success'] * 35} section embeddings for semantic search")
        print()
        print("Ready for:")
        print("  1. FastAPI backend development")
        print("  2. React frontend development")
        print("  3. Semantic search implementation")
        print("  4. RAG chatbot implementation")
    
    return results['failed'] == 0


if __name__ == "__main__":
    try:
        success = asyncio.run(process_all_fda_labels())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Batch processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
