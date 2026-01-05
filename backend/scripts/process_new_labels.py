"""
Process only new FDA labels that aren't in the database yet
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.etl.etl_builder import ETLBuilder
from backend.models.db_session import AsyncSessionLocal
from backend.models.database import DrugLabel
from sqlalchemy import select


async def get_existing_files():
    """Get list of files already processed"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(DrugLabel.source_file))
        return set(row[0] for row in result.all())


async def process_new_labels():
    """Process only new FDA labels"""
    
    print("\n" + "="*70)
    print("🔄 PROCESSING NEW FDA LABELS")
    print("="*70 + "\n")
    
    # Get existing files
    existing_files = await get_existing_files()
    print(f"✅ Already processed: {len(existing_files)} files")
    
    # Find all zip files
    raw_dir = project_root / "data" / "raw"
    all_files = sorted(raw_dir.glob("*.zip"))
    
    # Filter to only new files
    new_files = [f for f in all_files if f.name not in existing_files]
    
    if not new_files:
        print("\n✅ All files already processed! Nothing to do.")
        return
    
    print(f"🆕 Found {len(new_files)} new files to process:\n")
    for f in new_files:
        print(f"   🔵 {f.name}")
    
    print(f"\n{'='*70}")
    print("STARTING ETL PIPELINE")
    print("="*70 + "\n")
    
    # Initialize ETL builder
    builder = ETLBuilder()
    
    # Process each new file
    results = {
        'success': 0,
        'failed': 0,
        'drug_label_ids': []
    }
    
    for i, file_path in enumerate(new_files, 1):
        print(f"\n{'='*70}")
        print(f"Processing {i}/{len(new_files)}: {file_path.name}")
        print("="*70)
        
        drug_label_id = await builder.process_fda_label(str(file_path), file_path.name)
        
        if drug_label_id:
            results['success'] += 1
            results['drug_label_ids'].append(drug_label_id)
            print(f"✅ SUCCESS: Drug label ID {drug_label_id}")
        else:
            results['failed'] += 1
            print(f"❌ FAILED: Could not process {file_path.name}")
    
    # Final summary
    print(f"\n{'='*70}")
    print("📊 BATCH PROCESSING COMPLETE")
    print("="*70)
    print(f"✅ Successfully processed: {results['success']}/{len(new_files)}")
    print(f"❌ Failed: {results['failed']}/{len(new_files)}")
    
    if results['drug_label_ids']:
        print(f"\n🎉 New drug label IDs: {results['drug_label_ids']}")
    
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(process_new_labels())
