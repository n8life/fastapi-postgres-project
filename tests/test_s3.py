"""Tests for S3 functionality."""

import pytest
import pytest_asyncio
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import boto3
from moto import mock_aws
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.database import db_manager
from app.services.s3_service import S3Service


@pytest_asyncio.fixture
async def client():
    """Create test client with API key authentication"""
    # Set up test environment
    os.environ["API_KEY"] = "test-api-key-123"
    os.environ["ENFORCE_HTTPS"] = "false"
    
    headers = {"X-API-Key": "test-api-key-123"}
    async with AsyncClient(
        transport=ASGITransport(app=app), 
        base_url="http://test",
        headers=headers
    ) as ac:
        yield ac


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """Setup and teardown database for tests"""
    # Setup
    await db_manager.create_pool()
    yield
    # Teardown
    await db_manager.close_pool()


@pytest.fixture
def temp_issues_folder():
    """Create temporary issues folder for testing"""
    temp_dir = tempfile.mkdtemp()
    issues_path = Path(temp_dir) / "issues"
    issues_path.mkdir(exist_ok=True)
    
    yield issues_path
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def s3_environment():
    """Set up S3 environment variables for testing"""
    original_env = {}
    test_env = {
        "s3_region": "us-east-1",
        "s3_bucket_name": "test-security-logs",
        "s3_access_key": "test-access-key",
        "s3_secret_key": "test-secret-key"
    }
    
    # Store original values and set test values
    for key, value in test_env.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value
    
    yield test_env
    
    # Restore original values
    for key, original_value in original_env.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value


@pytest.fixture
def mock_s3_service(temp_issues_folder, s3_environment):
    """Create S3Service instance with temporary issues folder"""
    with patch('app.services.s3_service.Path') as mock_path:
        mock_path.return_value = temp_issues_folder
        service = S3Service()
        service.issues_folder = temp_issues_folder
        # Override with test environment values
        service.s3_bucket_name = s3_environment["s3_bucket_name"]
        service.s3_access_key = s3_environment["s3_access_key"]
        service.s3_secret_key = s3_environment["s3_secret_key"]
        service.s3_region = s3_environment["s3_region"]
        yield service


class TestS3Service:
    """Test cases for S3Service class."""
    
    def test_s3_service_initialization(self, s3_environment):
        """Test S3Service initialization with environment variables"""
        service = S3Service()
        
        assert service.s3_region == "us-east-1"
        assert service.s3_bucket_name == "test-security-logs"
        assert service.s3_access_key == "test-access-key"
        assert service.s3_secret_key == "test-secret-key"
    
    def test_s3_service_missing_credentials(self):
        """Test S3Service initialization with missing credentials"""
        # Clear environment variables
        env_vars = ["s3_region", "s3_bucket_name", "s3_access_key", "s3_secret_key"]
        original_values = {}
        
        for var in env_vars:
            original_values[var] = os.environ.get(var)
            os.environ.pop(var, None)
        
        try:
            service = S3Service()
            with pytest.raises(ValueError, match="Missing required S3 environment variables"):
                _ = service.s3_client
        finally:
            # Restore environment variables
            for var, value in original_values.items():
                if value is not None:
                    os.environ[var] = value
    
    @mock_aws
    def test_pull_file_from_s3_success(self, mock_s3_service, s3_environment):
        """Test successful file pull from S3"""
        # Set up mock S3
        s3_client = boto3.client('s3', region_name='us-east-1')
        bucket_name = s3_environment["s3_bucket_name"]
        s3_client.create_bucket(Bucket=bucket_name)
        
        # Upload test file to mock S3
        test_content = '{"test": "content", "sarif_version": "2.1.0"}'
        s3_filename = "test_file.sarif"
        s3_client.put_object(Bucket=bucket_name, Key=s3_filename, Body=test_content)
        
        # Mock the S3 client in our service
        mock_s3_service._s3_client = s3_client
        
        # Test file pull
        result = mock_s3_service.pull_file_from_s3(s3_filename)
        
        assert result["original_filename"] == s3_filename
        assert result["status"] == "success"
        assert result["file_size"] > 0
        assert result["local_filename"].endswith(".sarif")
        
        # Verify file was created locally
        local_file_path = mock_s3_service.issues_folder / result["local_filename"]
        assert local_file_path.exists()
        
        # Verify content
        with open(local_file_path, 'r') as f:
            content = f.read()
        assert content == test_content
    
    @mock_aws
    def test_pull_file_from_s3_file_not_found(self, mock_s3_service, s3_environment):
        """Test file pull when file doesn't exist in S3"""
        # Set up mock S3 with empty bucket
        s3_client = boto3.client('s3', region_name='us-east-1')
        bucket_name = s3_environment["s3_bucket_name"]
        s3_client.create_bucket(Bucket=bucket_name)
        
        mock_s3_service._s3_client = s3_client
        
        # Test file pull for non-existent file
        with pytest.raises(FileNotFoundError, match="not found in S3 bucket"):
            mock_s3_service.pull_file_from_s3("non_existent_file.sarif")
    
    @mock_aws
    def test_pull_file_from_s3_bucket_not_found(self, mock_s3_service, s3_environment):
        """Test file pull when bucket doesn't exist"""
        # Set up mock S3 without creating bucket
        s3_client = boto3.client('s3', region_name='us-east-1')
        mock_s3_service._s3_client = s3_client
        
        # Test file pull for non-existent bucket
        with pytest.raises(FileNotFoundError, match="S3 bucket .* not found"):
            mock_s3_service.pull_file_from_s3("test_file.sarif")
    
    def test_get_latest_file_content_success(self, mock_s3_service):
        """Test getting latest file content successfully"""
        # Create test files
        test_files = [
            ("older_file.sarif", '{"old": "content"}'),
            ("newer_file.sarif", '{"new": "content", "latest": true}')
        ]
        
        for filename, content in test_files:
            file_path = mock_s3_service.issues_folder / filename
            with open(file_path, 'w') as f:
                f.write(content)
        
        # Modify timestamps to ensure we can test "latest"
        import time
        older_file = mock_s3_service.issues_folder / "older_file.sarif"
        newer_file = mock_s3_service.issues_folder / "newer_file.sarif"
        
        # Set older file timestamp
        os.utime(older_file, (time.time() - 100, time.time() - 100))
        
        result = mock_s3_service.get_latest_file_content()
        
        assert result["filename"] == "newer_file.sarif"
        assert result["status"] == "success"
        assert "latest" in result["content"]
        assert result["file_size"] > 0
    
    def test_get_latest_file_content_no_files(self, mock_s3_service):
        """Test getting latest file content when no files exist"""
        with pytest.raises(FileNotFoundError, match="No files found in issues folder"):
            mock_s3_service.get_latest_file_content()
    
    def test_list_files_success(self, mock_s3_service):
        """Test listing files successfully"""
        # Create test files
        test_files = ["file1.sarif", "file2.sarif", "file3.txt"]
        for filename in test_files:
            file_path = mock_s3_service.issues_folder / filename
            with open(file_path, 'w') as f:
                f.write(f"content of {filename}")
        
        result = mock_s3_service.list_files()
        
        assert result["status"] == "success"
        assert result["count"] == 3
        assert len(result["files"]) == 3
        
        # Check that files are sorted by modification time (newest first)
        filenames = [f["filename"] for f in result["files"]]
        assert all(name in filenames for name in test_files)
    
    def test_list_files_empty_folder(self, mock_s3_service):
        """Test listing files in empty folder"""
        result = mock_s3_service.list_files()
        
        assert result["status"] == "success"
        assert result["count"] == 0
        assert result["files"] == []


class TestS3Endpoints:
    pytestmark = pytest.mark.anyio
    """Test cases for S3 API endpoints."""
    
    @mock_aws
    @patch('app.routers.s3.s3_service')
    async def test_pull_file_endpoint_success(self, mock_service, client):
        """Test successful file pull endpoint"""
        # Mock service response
        mock_service.pull_file_from_s3.return_value = {
            "local_filename": "12345678-1234-1234-1234-123456789abc.sarif",
            "original_filename": "test_file.sarif",
            "file_size": 1024,
            "status": "success"
        }
        
        response = await client.post("/s3/pull-file", json={"filename": "test_file.sarif"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["original_filename"] == "test_file.sarif"
        assert "Successfully pulled" in data["message"]
        
        mock_service.pull_file_from_s3.assert_called_once_with("test_file.sarif")
    
    @patch('app.routers.s3.s3_service')
    async def test_pull_file_endpoint_file_not_found(self, mock_service, client):
        """Test file pull endpoint when file not found"""
        mock_service.pull_file_from_s3.side_effect = FileNotFoundError("File not found")
        
        response = await client.post("/s3/pull-file", json={"filename": "missing_file.sarif"})
        
        assert response.status_code == 404
        assert "File not found" in response.json()["detail"]
    
    @patch('app.routers.s3.s3_service')
    async def test_pull_file_endpoint_credentials_error(self, mock_service, client):
        """Test file pull endpoint with credentials error"""
        from botocore.exceptions import NoCredentialsError
        mock_service.pull_file_from_s3.side_effect = NoCredentialsError()
        
        response = await client.post("/s3/pull-file", json={"filename": "test_file.sarif"})
        
        assert response.status_code == 401
        assert "credentials not found" in response.json()["detail"]
    
    @patch('app.routers.s3.s3_service')
    async def test_pull_file_endpoint_invalid_request(self, mock_service, client):
        """Test file pull endpoint with invalid request"""
        response = await client.post("/s3/pull-file", json={})
        
        assert response.status_code == 422  # Validation error
    
    @patch('app.routers.s3.s3_service')
    async def test_latest_file_endpoint_success(self, mock_service, client):
        """Test successful latest file endpoint"""
        # Mock service response
        mock_service.get_latest_file_content.return_value = {
            "filename": "latest_file.sarif",
            "content": '{"test": "content"}',
            "file_size": 20,
            "modified_time": 1635724800.0,
            "status": "success"
        }
        
        response = await client.get("/s3/latest-file")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["filename"] == "latest_file.sarif"
        assert data["content"] == '{"test": "content"}'
        
        mock_service.get_latest_file_content.assert_called_once()
    
    @patch('app.routers.s3.s3_service')
    async def test_latest_file_endpoint_no_files(self, mock_service, client):
        """Test latest file endpoint when no files exist"""
        mock_service.get_latest_file_content.side_effect = FileNotFoundError("No files found")
        
        response = await client.get("/s3/latest-file")
        
        assert response.status_code == 404
        assert "No files found" in response.json()["detail"]
    
    @patch('app.routers.s3.s3_service')
    async def test_list_files_endpoint_success(self, mock_service, client):
        """Test successful list files endpoint"""
        # Mock service response
        mock_service.list_files.return_value = {
            "files": [
                {"filename": "file1.sarif", "file_size": 100, "modified_time": 1635724800.0},
                {"filename": "file2.sarif", "file_size": 200, "modified_time": 1635724700.0}
            ],
            "count": 2,
            "status": "success"
        }
        
        response = await client.get("/s3/files")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["count"] == 2
        assert len(data["files"]) == 2
        
        mock_service.list_files.assert_called_once()
    
    async def test_endpoints_require_api_key(self, client):
        """Test that all endpoints require API key authentication"""
        # Create client without API key
        async with AsyncClient(
            transport=ASGITransport(app=app), 
            base_url="http://test"
        ) as no_key_client:
            
            # Test all endpoints
            endpoints = [
                ("POST", "/s3/pull-file", {"filename": "test.sarif"}),
                ("GET", "/s3/latest-file", None),
                ("GET", "/s3/files", None)
            ]
            
            for method, url, json_data in endpoints:
                if method == "POST":
                    response = await no_key_client.post(url, json=json_data)
                else:
                    response = await no_key_client.get(url)
                
                assert response.status_code in [401, 403], f"Endpoint {url} should require authentication"