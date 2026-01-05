"""
Reprocess All Labels Script
Re-parses all existing FDA labels with improved parsing logic
Updates drug names and dates in the database
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.etl.parser import FDAXMLParser
from backend.models.db_session import AsyncSessionLocal
from backend.models.database import DrugLabel
from sqlalchemy import select


async def reprocess_all_labels():
    """Reprocess all labels to fix drug names and dates"""
    
    print("\n" + "="*80)
    print("🔄 REPROCESSING ALL FDA LABELS")
    print("="*80 + "\n")
    
    parser = FDAXMLParser()
    raw_dir = project_root / "data" / "raw"
    
    if not raw_dir.exists():
        print(f"❌ ERROR: {raw_dir} not found")
        return
    
    async with AsyncSessionLocal() as session:
        # Get all drug labels
        result = await session.execute(select(DrugLabel).order_by(DrugLabel.id))
        all_labels = result.scalars().all()
        
        print(f"📋 Found {len(all_labels)} drug labels in database\n")
        
        updated_count = 0
        failed_count = 0
        
        for drug_label in all_labels:
            print(f"Processing ID {drug_label.id}: {drug_label.source_file}")
            
            # Find the source file
            zip_file = raw_dir / drug_label.source_file
            
            if not zip_file.exists():
                print(f"   ⚠️  File not found: {zip_file}")
                failed_count += 1
                continue
            
            # Re-parse the XML
            parsed_data = parser.parse_zip_file(str(zip_file))
            
            if not parsed_data:
                print(f"   ❌ Failed to parse")
                failed_count += 1
                continue
            
            metadata = parsed_data['metadata']
            
            # Extract new values
            new_name = metadata.get('name', drug_label.name)
            effective_time_str = metadata.get('effective_time', '')
            
            # Parse date
            new_last_updated = None
            if effective_time_str:
                try:
                    new_last_updated = datetime.strptime(effective_time_str, '%Y%m%d')
                except ValueError:
                    print(f"   ⚠️  Could not parse date: {effective_time_str}")
            
            # Show changes
            changes = []
            if new_name != drug_label.name:
                changes.append(f"name: '{drug_label.name}' → '{new_name}'")
            if new_last_updated and new_last_updated != drug_label.last_updated:
                old_date = drug_label.last_updated.strftime('%Y-%m-%d') if drug_label.last_updated else 'None'
                new_date = new_last_updated.strftime('%Y-%m-%d')
                changes.append(f"last_updated: {old_date} → {new_date}")
            
            if changes:
                print(f"   🔄 Updates:")
                for change in changes:
                    print(f"      • {change}")
                
                # Update database
                drug_label.name = new_name
                if new_last_updated:
                    drug_label.last_updated = new_last_updated
                
                updated_count += 1
            else:
                print(f"   ✅ No changes needed")
            
            print()
        
        # Commit all changes
        await session.commit()
        
        print("="*80)
        print("📊 REPROCESSING SUMMARY")
        print("="*80)
        print(f"✅ Successfully updated: {updated_count}")
        print(f"⚠️  Failed: {failed_count}")
        print(f"📋 Total processed: {len(all_labels)}")
        print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(reprocess_all_labels())
