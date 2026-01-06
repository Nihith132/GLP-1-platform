"""
S3 Uploader Service
Handles uploading label ZIPs to AWS S3
"""

import boto3
import os
from pathlib import Path
from datetime import datetime
from typing import Optional


class S3Uploader:
    """Uploads label files to S3 with organized folder structure"""
    
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        self.bucket_name = os.getenv('S3_BUCKET_NAME')
        
        if not self.bucket_name:
            raise ValueError("S3_BUCKET_NAME environment variable not set")
    
    async def upload_label(
        self,
        zip_path: Path,
        drug_id: int,
        set_id: str,
        version: str
    ) -> Optional[str]:
        """
        Upload label ZIP to S3
        
        Folder structure: labels/active/{set_id}/v{version}/{set_id}_v{version}.zip
        
        Returns S3 key if successful, None otherwise
        """
        try:
            # Construct S3 key
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            s3_key = f"labels/active/{set_id}/v{version}/{set_id}_v{version}_{timestamp}.zip"
            
            # Upload with metadata
            self.s3_client.upload_file(
                str(zip_path),
                self.bucket_name,
                s3_key,
                ExtraArgs={
                    'Metadata': {
                        'drug_id': str(drug_id),
                        'set_id': set_id,
                        'version': version,
                        'upload_date': timestamp
                    }
                }
            )
            
            return s3_key
        
        except Exception as e:
            print(f"         S3 upload error: {str(e)}")
            return None
    
    async def archive_old_version(
        self,
        set_id: str,
        old_version: str
    ):
        """
        Move old version from active/ to archive/
        
        Keeps last 5 versions in active, older ones go to archive
        """
        try:
            # List all versions for this SET_ID
            prefix = f"labels/active/{set_id}/"
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            if 'Contents' not in response:
                return
            
            # Sort by version (newest first)
            objects = sorted(
                response['Contents'],
                key=lambda x: x['LastModified'],
                reverse=True
            )
            
            # Archive versions beyond the 5 most recent
            for obj in objects[5:]:
                old_key = obj['Key']
                new_key = old_key.replace('labels/active/', 'labels/archive/')
                
                # Copy to archive
                self.s3_client.copy_object(
                    Bucket=self.bucket_name,
                    CopySource={'Bucket': self.bucket_name, 'Key': old_key},
                    Key=new_key
                )
                
                # Delete from active
                self.s3_client.delete_object(
                    Bucket=self.bucket_name,
                    Key=old_key
                )
                
                print(f"         Archived: {old_key} → {new_key}")
        
        except Exception as e:
            print(f"         Archive error: {str(e)}")
    
    async def upload_log(
        self,
        log_path: Path,
        run_timestamp: str
    ) -> Optional[str]:
        """
        Upload watchdog log file to S3
        
        Folder: logs/watchdog/{YYYYMMDD}/watchdog_{timestamp}.log
        """
        try:
            date_prefix = datetime.utcnow().strftime('%Y%m%d')
            s3_key = f"logs/watchdog/{date_prefix}/watchdog_{run_timestamp}.log"
            
            self.s3_client.upload_file(
                str(log_path),
                self.bucket_name,
                s3_key
            )
            
            return s3_key
        
        except Exception as e:
            print(f"         Log upload error: {str(e)}")
            return None
