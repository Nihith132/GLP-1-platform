"""
FDA Label Upload Script
Uploads downloaded FDA label files from data/raw/ to S3
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.services.s3_client import s3_client
from backend.core.config import settings


def upload_fda_labels():
    """Upload all FDA label files from data/raw/ to S3"""
    
    print("=" * 60)
    print("📤 FDA LABEL UPLOAD TO S3")
    print("=" * 60)
    print()
    
    # Define the data/raw directory
    raw_data_dir = project_root / "data" / "raw"
    
    if not raw_data_dir.exists():
        print(f"❌ ERROR: Directory not found: {raw_data_dir}")
        print("Please create the 'data/raw' folder and place your FDA label files there.")
        return False
    
    # Find all zip files
    zip_files = list(raw_data_dir.glob("*.zip"))
    xml_files = list(raw_data_dir.glob("*.xml"))
    all_files = zip_files + xml_files
    
    if not all_files:
        print(f"❌ No .zip or .xml files found in: {raw_data_dir}")
        print()
        print("Please download FDA label files and save them to:")
        print(f"   {raw_data_dir}")
        print()
        print("Download from: https://dailymed.nlm.nih.gov/")
        return False
    
    print(f"📁 Found {len(all_files)} file(s) to upload:")
    for f in all_files:
        print(f"   • {f.name}")
    print()
    
    # Upload each file
    uploaded = 0
    failed = 0
    
    for file_path in all_files:
        file_name = file_path.name
        
        # Create S3 key with structure: raw/filename
        s3_key = f"raw/{file_name}"
        
        print(f"Uploading: {file_name}...")
        
        # Add metadata
        metadata = {
            "source": "FDA DailyMed",
            "uploaded_by": "manual_upload_script",
            "original_filename": file_name
        }
        
        success = s3_client.upload_file(
            str(file_path),
            s3_key,
            metadata=metadata
        )
        
        if success:
            print(f"   ✅ SUCCESS: Uploaded to s3://{settings.S3_BUCKET_NAME}/{s3_key}")
            uploaded += 1
        else:
            print(f"   ❌ FAILED: Could not upload {file_name}")
            failed += 1
        print()
    
    # Summary
    print("=" * 60)
    print("📊 UPLOAD SUMMARY")
    print("=" * 60)
    print(f"✅ Successfully uploaded: {uploaded} file(s)")
    if failed > 0:
        print(f"❌ Failed to upload: {failed} file(s)")
    print()
    
    if uploaded > 0:
        print("🎉 Files are now in S3 and ready for processing!")
        print()
        print("Next step: Run the ETL pipeline to process these files")
        print("Command: python backend/etl/builder.py")
    
    return failed == 0


def list_uploaded_files():
    """List all files currently in S3"""
    
    print()
    print("=" * 60)
    print("📋 FILES CURRENTLY IN S3 BUCKET")
    print("=" * 60)
    print()
    
    objects = s3_client.list_objects(prefix="raw/")
    
    if not objects:
        print("No files found in S3 bucket under 'raw/' prefix")
    else:
        print(f"Found {len(objects)} file(s):")
        for obj in objects:
            size_mb = obj['size'] / (1024 * 1024)
            print(f"   • {obj['key']}")
            print(f"     Size: {size_mb:.2f} MB | Modified: {obj['last_modified']}")
        print()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Upload FDA label files to S3")
    parser.add_argument(
        "--list",
        action="store_true",
        help="List files already in S3 (don't upload)"
    )
    
    args = parser.parse_args()
    
    try:
        if args.list:
            list_uploaded_files()
        else:
            success = upload_fda_labels()
            if success:
                list_uploaded_files()
            sys.exit(0 if success else 1)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Upload interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
