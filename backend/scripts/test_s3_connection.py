"""
S3 Connection Test Script
Tests AWS S3 connectivity and bucket access
Run this to verify your AWS credentials are working correctly
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.services.s3_client import s3_client
from backend.core.config import settings


def test_s3_connection():
    """Test S3 connection and bucket access"""
    
    print("=" * 60)
    print("🧪 AWS S3 CONNECTION TEST")
    print("=" * 60)
    print()
    
    # Display configuration
    print("📋 Configuration:")
    print(f"   Bucket Name: {settings.S3_BUCKET_NAME}")
    print(f"   Region: {settings.AWS_REGION}")
    print(f"   Access Key: {settings.AWS_ACCESS_KEY_ID[:10]}...")
    print()
    
    # Test 1: Check if bucket exists
    print("Test 1: Checking if bucket exists...")
    try:
        exists = s3_client.bucket_exists()
        if exists:
            print("   ✅ SUCCESS: Bucket exists and is accessible!")
        else:
            print("   ❌ FAILED: Bucket does not exist")
            return False
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False
    print()
    
    # Test 2: List objects in bucket
    print("Test 2: Listing objects in bucket...")
    try:
        objects = s3_client.list_objects()
        if len(objects) == 0:
            print("   ℹ️  Bucket is empty (this is normal for a new bucket)")
        else:
            print(f"   ✅ Found {len(objects)} objects:")
            for obj in objects[:5]:  # Show first 5
                print(f"      - {obj['key']} ({obj['size']} bytes)")
            if len(objects) > 5:
                print(f"      ... and {len(objects) - 5} more")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False
    print()
    
    # Test 3: Test upload (create a dummy file)
    print("Test 3: Testing upload capability...")
    test_content = "This is a test file from GLP-1 Platform"
    test_key = "test/connection_test.txt"
    
    try:
        # Create a temporary file
        temp_file = Path("temp_test_file.txt")
        temp_file.write_text(test_content)
        
        # Upload it
        success = s3_client.upload_file(
            str(temp_file),
            test_key,
            metadata={"test": "true", "created_by": "test_script"}
        )
        
        if success:
            print(f"   ✅ SUCCESS: Uploaded test file to '{test_key}'")
        else:
            print("   ❌ FAILED: Could not upload test file")
            return False
        
        # Clean up local file
        temp_file.unlink()
        
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False
    print()
    
    # Test 4: Test download
    print("Test 4: Testing download capability...")
    try:
        file_obj = s3_client.download_fileobj(test_key)
        if file_obj:
            content = file_obj.read().decode('utf-8')
            if content == test_content:
                print("   ✅ SUCCESS: Downloaded and verified test file")
            else:
                print("   ❌ FAILED: Downloaded content doesn't match")
                return False
        else:
            print("   ❌ FAILED: Could not download test file")
            return False
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False
    print()
    
    # Test 5: Cleanup - delete test file
    print("Test 5: Cleaning up test file...")
    try:
        success = s3_client.delete_object(test_key)
        if success:
            print("   ✅ SUCCESS: Test file deleted")
        else:
            print("   ⚠️  WARNING: Could not delete test file (not critical)")
    except Exception as e:
        print(f"   ⚠️  WARNING: {e}")
    print()
    
    # Final summary
    print("=" * 60)
    print("🎉 ALL TESTS PASSED!")
    print("=" * 60)
    print()
    print("✅ Your AWS S3 connection is working perfectly!")
    print("✅ You can now upload FDA drug label files to your bucket")
    print()
    print("Next steps:")
    print("1. Download FDA drug label XML files from DailyMed")
    print("2. Place them in the 'data/raw/' folder")
    print("3. Run the upload script to move them to S3")
    print()
    
    return True


if __name__ == "__main__":
    try:
        success = test_s3_connection()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
