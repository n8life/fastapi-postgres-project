"""S3 service for handling AWS S3 file operations."""

import os
import uuid
from pathlib import Path
from typing import Dict, Any
import boto3
from botocore.exceptions import ClientError, NoCredentialsError


class S3Service:
    """Service for handling S3 file operations."""
    
    def __init__(self):
        """Initialize S3 service with environment configuration."""
        self.s3_region = os.getenv("s3_region", "us-east-1")
        self.s3_bucket_name = os.getenv("s3_bucket_name")
        self.s3_access_key = os.getenv("s3_access_key")
        self.s3_secret_key = os.getenv("s3_secret_key")
        self.issues_folder = Path("issues")
        
        # Ensure issues folder exists
        self.issues_folder.mkdir(exist_ok=True)
        
        # Initialize S3 client
        self._s3_client = None
    
    @property
    def s3_client(self):
        """Lazy initialization of S3 client."""
        if self._s3_client is None:
            if not all([self.s3_access_key, self.s3_secret_key, self.s3_bucket_name]):
                raise ValueError("Missing required S3 environment variables")
            
            self._s3_client = boto3.client(
                's3',
                aws_access_key_id=self.s3_access_key,
                aws_secret_access_key=self.s3_secret_key,
                region_name=self.s3_region
            )
        return self._s3_client
    
    def pull_file_from_s3(self, s3_filename: str) -> Dict[str, Any]:
        """
        Pull a file from S3 and save it locally with UUID-based name.
        
        Args:
            s3_filename: Name of the file in S3 bucket
            
        Returns:
            Dict with local filename, original filename, and file size
            
        Raises:
            ClientError: If S3 operation fails
            NoCredentialsError: If AWS credentials are invalid
        """
        try:
            # Generate UUID-based filename with .sarif extension
            unique_id = str(uuid.uuid4())
            local_filename = f"{unique_id}.sarif"
            local_filepath = self.issues_folder / local_filename
            
            # Download file from S3
            self.s3_client.download_file(
                self.s3_bucket_name,
                s3_filename,
                str(local_filepath)
            )
            
            # Get file size
            file_size = local_filepath.stat().st_size
            
            return {
                "local_filename": local_filename,
                "original_filename": s3_filename,
                "file_size": file_size,
                "status": "success"
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                raise FileNotFoundError(f"File '{s3_filename}' not found in S3 bucket '{self.s3_bucket_name}'") from e
            elif error_code == 'NoSuchBucket':
                raise FileNotFoundError(f"S3 bucket '{self.s3_bucket_name}' not found") from e
            else:
                raise ClientError(f"S3 operation failed: {e.response['Error']['Message']}", e.response['Error']) from e
                
        except NoCredentialsError as e:
            raise NoCredentialsError("AWS credentials not found or invalid") from e
    
    def get_latest_file_content(self) -> Dict[str, Any]:
        """
        Get the content of the latest file in the issues folder.
        
        Returns:
            Dict with filename, content, and metadata
            
        Raises:
            FileNotFoundError: If no files found in issues folder
        """
        # Get all files in issues folder
        files = [f for f in self.issues_folder.iterdir() if f.is_file()]
        
        if not files:
            raise FileNotFoundError("No files found in issues folder")
        
        # Find the latest file by modification time
        latest_file = max(files, key=lambda f: f.stat().st_mtime)
        
        try:
            # Read file content
            with open(latest_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Get file metadata
            stat = latest_file.stat()
            
            return {
                "filename": latest_file.name,
                "content": content,
                "file_size": stat.st_size,
                "modified_time": stat.st_mtime,
                "status": "success"
            }
            
        except UnicodeDecodeError:
            # Handle binary files
            with open(latest_file, 'rb') as f:
                content = f.read()
            
            return {
                "filename": latest_file.name,
                "content": content.decode('utf-8', errors='replace'),
                "file_size": stat.st_size,
                "modified_time": stat.st_mtime,
                "status": "success",
                "note": "File content was decoded with error replacement"
            }
    
    def list_files(self) -> Dict[str, Any]:
        """
        List all files in the issues folder.
        
        Returns:
            Dict with list of files and their metadata
        """
        files = []
        for file_path in self.issues_folder.iterdir():
            if file_path.is_file():
                stat = file_path.stat()
                files.append({
                    "filename": file_path.name,
                    "file_size": stat.st_size,
                    "modified_time": stat.st_mtime
                })
        
        # Sort by modification time (newest first)
        files.sort(key=lambda x: x["modified_time"], reverse=True)
        
        return {
            "files": files,
            "count": len(files),
            "status": "success"
        }


# Global instance
s3_service = S3Service()