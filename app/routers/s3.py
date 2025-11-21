"""S3 router for handling S3 file operations."""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError, NoCredentialsError

from ..security import get_api_key
from ..services.s3_service import s3_service


router = APIRouter(prefix="/s3", tags=["s3"])


class PullFileRequest(BaseModel):
    """Request model for pulling file from S3."""
    filename: str
    

class PullFileResponse(BaseModel):
    """Response model for pull file operation."""
    local_filename: str
    original_filename: str
    file_size: int
    status: str
    message: str


class LatestFileResponse(BaseModel):
    """Response model for latest file content."""
    filename: str
    content: str
    file_size: int
    modified_time: float
    status: str
    note: Optional[str] = None


class FileListResponse(BaseModel):
    """Response model for file listing."""
    files: list[Dict[str, Any]]
    count: int
    status: str


@router.post("/pull-file", response_model=PullFileResponse)
async def pull_file_from_s3(
    request: PullFileRequest,
    api_key: str = Depends(get_api_key)
) -> PullFileResponse:
    """
    Pull a file from S3 bucket and save it to issues folder with UUID-based name.
    
    Args:
        request: Request containing the S3 filename to pull
        api_key: API key for authentication
        
    Returns:
        Response with local filename and operation details
        
    Raises:
        HTTPException: For various error conditions
    """
    try:
        result = s3_service.pull_file_from_s3(request.filename)
        
        return PullFileResponse(
            local_filename=result["local_filename"],
            original_filename=result["original_filename"],
            file_size=result["file_size"],
            status=result["status"],
            message=f"Successfully pulled '{request.filename}' from S3 and saved as '{result['local_filename']}'"
        )
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Configuration error: {str(e)}")
    
    except NoCredentialsError:
        raise HTTPException(status_code=401, detail="AWS credentials not found or invalid")
    
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"S3 operation failed: {str(e)}")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.get("/latest-file", response_model=LatestFileResponse)
async def get_latest_file_content(
    api_key: str = Depends(get_api_key)
) -> LatestFileResponse:
    """
    Read and return the content of the latest file from issues folder.
    
    Args:
        api_key: API key for authentication
        
    Returns:
        Response with file content and metadata
        
    Raises:
        HTTPException: For various error conditions
    """
    try:
        result = s3_service.get_latest_file_content()
        
        return LatestFileResponse(
            filename=result["filename"],
            content=result["content"],
            file_size=result["file_size"],
            modified_time=result["modified_time"],
            status=result["status"],
            note=result.get("note")
        )
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")


@router.get("/files", response_model=FileListResponse)
async def list_files(
    api_key: str = Depends(get_api_key)
) -> FileListResponse:
    """
    List all files in the issues folder.
    
    Args:
        api_key: API key for authentication
        
    Returns:
        Response with list of files and metadata
    """
    try:
        result = s3_service.list_files()
        
        return FileListResponse(
            files=result["files"],
            count=result["count"],
            status=result["status"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing files: {str(e)}")