"""
Watchdog Pipeline Entry Point
Runs version checks, downloads, S3 uploads, and ETL processing
"""

import asyncio
import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.watchdog.version_checker import VersionChecker
from services.watchdog.s3_uploader import S3Uploader
from services.watchdog.notifier import Notifier
from models.db_session import AsyncSessionLocal


async def run_watchdog_pipeline(mode: str = 'daily'):
    """
    Main watchdog pipeline execution
    
    Args:
        mode: 'daily' (check all enabled drugs) or 'manual' (check specific SET_ID)
    """
    start_time = datetime.utcnow()
    print(f"\n{'='*60}")
    print(f"🐕 Watchdog Pipeline Started - {start_time.isoformat()}")
    print(f"Mode: {mode.upper()}")
    print(f"{'='*60}\n")
    
    # Initialize services
    version_checker = VersionChecker()
    s3_uploader = S3Uploader()
    notifier = Notifier()
    
    set_id = os.getenv('SET_ID')
    force_download = os.getenv('FORCE_DOWNLOAD', 'false').lower() == 'true'
    
    try:
        # Step 1: Get drugs to check
        print("📋 Step 1: Fetching drugs to check...")
        async with AsyncSessionLocal() as session:
            if mode == 'manual' and set_id:
                drugs_to_check = await version_checker.get_specific_drug(session, set_id)
                print(f"   ✓ Checking specific drug: {set_id}")
            else:
                drugs_to_check = await version_checker.get_enabled_drugs(session)
                print(f"   ✓ Found {len(drugs_to_check)} enabled drugs")
        
        if not drugs_to_check:
            print("   ⚠️  No drugs to check. Exiting.")
            return
        
        # Step 2: Check each drug for version updates
        print(f"\n🔍 Step 2: Checking versions via DailyMed API...")
        results = {
            'new_versions': [],
            'up_to_date': [],
            'errors': []
        }
        
        for drug in drugs_to_check:
            print(f"\n   Checking: {drug['drug_name']} (SET_ID: {drug['set_id']})")
            
            result = await version_checker.check_version(
                drug_id=drug['drug_id'],
                set_id=drug['set_id'],
                current_version=drug['current_version']
            )
            
            if result['status'] == 'new_version':
                results['new_versions'].append(result)
                print(f"      🆕 New version found: {result['new_version']}")
                print(f"      📅 Published: {result['publish_date']}")
            elif result['status'] == 'up_to_date':
                results['up_to_date'].append(result)
                print(f"      ✓ Up to date: {result['current_version']}")
            else:
                results['errors'].append(result)
                print(f"      ❌ Error: {result.get('error', 'Unknown')}")
        
        # Step 3: Download and upload new versions to S3
        if results['new_versions']:
            print(f"\n📦 Step 3: Processing {len(results['new_versions'])} new versions...")
            
            for result in results['new_versions']:
                print(f"\n   Processing: {result['drug_name']}")
                
                # Download ZIP
                print(f"      ⬇️  Downloading from DailyMed...")
                zip_path = await version_checker.download_label_zip(
                    set_id=result['set_id'],
                    version=result['new_version']
                )
                
                if zip_path:
                    print(f"      ✓ Downloaded to: {zip_path}")
                    
                    # Upload to S3
                    print(f"      ⬆️  Uploading to S3...")
                    s3_key = await s3_uploader.upload_label(
                        zip_path=zip_path,
                        drug_id=result['drug_id'],
                        set_id=result['set_id'],
                        version=result['new_version']
                    )
                    
                    if s3_key:
                        print(f"      ✓ Uploaded to S3: {s3_key}")
                        result['s3_key'] = s3_key
                        
                        # Update database with new version
                        async with AsyncSessionLocal() as session:
                            await version_checker.save_version_update(
                                session=session,
                                drug_id=result['drug_id'],
                                old_version=result['current_version'],
                                new_version=result['new_version'],
                                s3_key=s3_key,
                                publish_date=result['publish_date']
                            )
                        print(f"      ✓ Database updated")
                    else:
                        print(f"      ❌ S3 upload failed")
                        results['errors'].append({
                            **result,
                            'error': 'S3 upload failed'
                        })
                else:
                    print(f"      ❌ Download failed")
                    results['errors'].append({
                        **result,
                        'error': 'Download failed'
                    })
        else:
            print(f"\n✓ Step 3: No new versions to process")
        
        # Step 4: Send notifications
        print(f"\n📧 Step 4: Sending notifications...")
        
        if results['new_versions'] or results['errors']:
            await notifier.send_summary(
                new_versions=results['new_versions'],
                up_to_date=results['up_to_date'],
                errors=results['errors'],
                mode=mode
            )
            print(f"   ✓ Notifications sent")
        else:
            print(f"   ℹ️  No notifications needed (all up to date)")
        
        # Summary
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        print(f"\n{'='*60}")
        print(f"✅ Watchdog Pipeline Completed")
        print(f"{'='*60}")
        print(f"Duration: {duration:.2f} seconds")
        print(f"New Versions: {len(results['new_versions'])}")
        print(f"Up to Date: {len(results['up_to_date'])}")
        print(f"Errors: {len(results['errors'])}")
        print(f"{'='*60}\n")
        
        # Exit with error if there were issues
        if results['errors']:
            sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {str(e)}")
        
        # Send error notification
        await notifier.send_error(
            error_message=str(e),
            mode=mode,
            set_id=set_id
        )
        
        sys.exit(1)


def main():
    """Parse arguments and run pipeline"""
    parser = argparse.ArgumentParser(description='Watchdog Label Version Checker')
    parser.add_argument(
        '--mode',
        choices=['daily', 'manual'],
        default='daily',
        help='Check mode: daily (all enabled) or manual (specific SET_ID)'
    )
    
    args = parser.parse_args()
    
    # Run async pipeline
    asyncio.run(run_watchdog_pipeline(mode=args.mode))


if __name__ == '__main__':
    main()
