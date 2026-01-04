"""
AWS S3 Client Service
Handles all interactions with S3 bucket for raw FDA label storage
"""

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from typing import List, Optional, BinaryIO
import io
import logging
from pathlib import Path

from backend.core.config import settings

logger = logging.getLogger(__name__)


class S3Client:
    """
    Robust S3 client for managing FDA label files
    Handles upload, download, listing, and versioning
    """
    
    def __init__(self):
        """Initialize S3 client with credentials from settings"""
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )
            self.bucket_name = settings.S3_BUCKET_NAME
            logger.info(f"S3 Client initialized for bucket: {self.bucket_name}")
        except NoCredentialsError:
            logger.error("AWS credentials not found. Check your .env file.")
            raise
    
    def bucket_exists(self) -> bool:
        """Check if the configured bucket exists"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                return False
            logger.error(f"Error checking bucket: {e}")
            raise
    
    def create_bucket(self) -> bool:
        """
        Create the S3 bucket if it doesn't exist
        Returns True if created, False if already exists
        """
        if self.bucket_exists():
            logger.info(f"Bucket {self.bucket_name} already exists")
            return False
        
        try:
            if settings.AWS_REGION == 'us-east-1':
                self.s3_client.create_bucket(Bucket=self.bucket_name)
            else:
                self.s3_client.create_bucket(
                    Bucket=self.bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': settings.AWS_REGION}
                )
            logger.info(f"Created bucket: {self.bucket_name}")
            return True
        except ClientError as e:
            logger.error(f"Failed to create bucket: {e}")
            raise
    
    def upload_file(
        self, 
        file_path: str, 
        s3_key: str,
        metadata: Optional[dict] = None
    ) -> bool:
        """
        Upload a file to S3
        
        Args:
            file_path: Local file path
            s3_key: S3 object key (e.g., "ozempic/v1_2024.zip")
            metadata: Optional metadata dict
        
        Returns:
            True if successful
        """
        try:
            extra_args = {}
            if metadata:
                extra_args['Metadata'] = metadata
            
            self.s3_client.upload_file(
                file_path,
                self.bucket_name,
                s3_key,
                ExtraArgs=extra_args
            )
            logger.info(f"Uploaded {file_path} to s3://{self.bucket_name}/{s3_key}")
            return True
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return False
        except ClientError as e:
            logger.error(f"Failed to upload file: {e}")
            return False
    
    def upload_fileobj(
        self,
        file_obj: BinaryIO,
        s3_key: str,
        metadata: Optional[dict] = None
    ) -> bool:
        """
        Upload a file-like object to S3 (useful for in-memory files)
        
        Args:
            file_obj: File-like object (BytesIO, etc.)
            s3_key: S3 object key
            metadata: Optional metadata
        """
        try:
            extra_args = {}
            if metadata:
                extra_args['Metadata'] = metadata
            
            self.s3_client.upload_fileobj(
                file_obj,
                self.bucket_name,
                s3_key,
                ExtraArgs=extra_args
            )
            logger.info(f"Uploaded file object to s3://{self.bucket_name}/{s3_key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to upload file object: {e}")
            return False
    
    def download_file(self, s3_key: str, local_path: str) -> bool:
        """
        Download a file from S3 to local disk
        
        Args:
            s3_key: S3 object key
            local_path: Local file path to save to
        """
        try:
            # Create parent directories if they don't exist
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            
            self.s3_client.download_file(
                self.bucket_name,
                s3_key,
                local_path
            )
            logger.info(f"Downloaded s3://{self.bucket_name}/{s3_key} to {local_path}")
            return True
        except ClientError as e:
            logger.error(f"Failed to download file: {e}")
            return False
    
    def download_fileobj(self, s3_key: str) -> Optional[io.BytesIO]:
        """
        Download a file from S3 directly to memory (BytesIO)
        Useful for processing without disk writes
        
        Args:
            s3_key: S3 object key
        
        Returns:
            BytesIO object or None if failed
        """
        try:
            file_obj = io.BytesIO()
            self.s3_client.download_fileobj(
                self.bucket_name,
                s3_key,
                file_obj
            )
            file_obj.seek(0)  # Reset pointer to beginning
            logger.info(f"Downloaded s3://{self.bucket_name}/{s3_key} to memory")
            return file_obj
        except ClientError as e:
            logger.error(f"Failed to download file to memory: {e}")
            return None
    
    def list_objects(self, prefix: str = "") -> List[dict]:
        """
        List all objects in bucket with optional prefix filter
        
        Args:
            prefix: Filter by key prefix (e.g., "ozempic/" for all Ozempic files)
        
        Returns:
            List of dicts with 'Key', 'Size', 'LastModified'
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            if 'Contents' not in response:
                return []
            
            objects = [
                {
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified']
                }
                for obj in response['Contents']
            ]
            logger.info(f"Found {len(objects)} objects with prefix '{prefix}'")
            return objects
        except ClientError as e:
            logger.error(f"Failed to list objects: {e}")
            return []
    
    def delete_object(self, s3_key: str) -> bool:
        """
        Delete an object from S3
        Use with caution - this is permanent!
        
        Args:
            s3_key: S3 object key to delete
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            logger.warning(f"Deleted s3://{self.bucket_name}/{s3_key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete object: {e}")
            return False
    
    def get_object_metadata(self, s3_key: str) -> Optional[dict]:
        """
        Get metadata for an S3 object without downloading it
        
        Args:
            s3_key: S3 object key
        
        Returns:
            Dict with metadata or None if not found
        """
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return {
                'size': response['ContentLength'],
                'last_modified': response['LastModified'],
                'content_type': response.get('ContentType'),
                'metadata': response.get('Metadata', {})
            }
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                logger.warning(f"Object not found: {s3_key}")
            else:
                logger.error(f"Failed to get object metadata: {e}")
            return None
    
    def object_exists(self, s3_key: str) -> bool:
        """Check if an object exists in S3"""
        return self.get_object_metadata(s3_key) is not None


# Singleton instance
s3_client = S3Client()
