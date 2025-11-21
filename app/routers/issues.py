"""
Issues router for handling files in the issues directory.
"""
from fastapi import APIRouter, HTTPException, Depends, status
import logging

from ..security import get_api_key
from ..services.issues_service import issues_service
from ..schemas.issues import (
    IssueFilesResponse, 
    IssueFileInfo,
    ProcessFileRequest, 
    ProcessedFileResponse,
    FileContentResponse,
    ProcessAllFilesResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/issues",
    tags=["issues"],
    responses={
        401: {"description": "Invalid API key"},
        500: {"description": "Internal server error"}
    }
)


@router.get("/files", response_model=IssueFilesResponse)
async def list_issues_files(api_key: str = Depends(get_api_key)):
    """
    Get list of all files in the issues directory.
    
    Returns information about each file including name, size, and modification date.
    """
    try:
        logger.info("Listing files in issues directory")
        files = issues_service.get_issues_files()
        
        file_infos = [
            IssueFileInfo(
                filename=file["filename"],
                file_path=file["file_path"],
                size=file["size"],
                modified=file["modified"],
                file_type=file["file_type"]
            )
            for file in files
        ]
        
        return IssueFilesResponse(
            files=file_infos,
            total_count=len(file_infos)
        )
    
    except Exception as e:
        logger.error(f"Error listing issues files: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list issues files: {str(e)}"
        )


@router.get("/files/{filename}/content", response_model=FileContentResponse)
async def get_file_content(filename: str, api_key: str = Depends(get_api_key)):
    """
    Get the parsed content of a specific file from the issues directory.
    
    Args:
        filename: Name of the file to read
        
    Returns:
        Parsed content of the file based on its type (CSV, JSON, etc.)
    """
    try:
        logger.info(f"Reading content of file: {filename}")
        content_data = issues_service.read_file_content(filename)
        
        return FileContentResponse(
            filename=content_data.get("filename", filename),
            file_type=content_data.get("file_type", "unknown"),
            content=content_data
        )
    
    except FileNotFoundError:
        logger.warning(f"File not found: {filename}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File '{filename}' not found in issues directory"
        )
    
    except ValueError as e:
        error_msg = str(e)
        if any(pattern in error_msg for pattern in [
            "Path traversal detected", "Invalid filename", 
            "Hidden files are not allowed", "Filename contains null bytes"
        ]):
            logger.warning(f"Security violation attempt - {error_msg}: {filename}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename"
            )
        else:
            logger.error(f"Error reading file {filename}: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
    
    except Exception as e:
        logger.error(f"Unexpected error reading file {filename}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read file content: {str(e)}"
        )


@router.post("/process-file", response_model=ProcessedFileResponse)
async def process_file(request: ProcessFileRequest, api_key: str = Depends(get_api_key)):
    """
    Process a specific file and create a message record in the database.
    
    Args:
        request: Request containing the filename to process
        
    Returns:
        Information about the created message record
    """
    try:
        logger.info(f"Processing file: {request.filename}")
        result = await issues_service.create_message_from_file(request.filename)
        
        return ProcessedFileResponse(
            message_id=result["message_id"],
            filename=result["filename"],
            message_type=result["message_type"],
            created_at=result["created_at"],
            content_preview=result["content_preview"]
        )
    
    except FileNotFoundError:
        logger.warning(f"File not found: {request.filename}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File '{request.filename}' not found in issues directory"
        )
    
    except ValueError as e:
        error_msg = str(e)
        if any(pattern in error_msg for pattern in [
            "Path traversal detected", "Invalid filename", 
            "Hidden files are not allowed", "Filename contains null bytes"
        ]):
            logger.warning(f"Security violation attempt - {error_msg}: {request.filename}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename"
            )
        else:
            logger.error(f"Error processing file {request.filename}: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
    
    except Exception as e:
        logger.error(f"Unexpected error processing file {request.filename}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process file: {str(e)}"
        )


@router.post("/process-all", response_model=ProcessAllFilesResponse)
async def process_all_files(api_key: str = Depends(get_api_key)):
    """
    Process all files in the issues directory and create message records.
    
    Returns:
        Summary of all processed files and any errors encountered
    """
    try:
        logger.info("Processing all files in issues directory")
        
        # Get list of files
        files = issues_service.get_issues_files()
        processed_files = []
        errors = []
        
        for file_info in files:
            try:
                result = await issues_service.create_message_from_file(file_info["filename"])
                processed_files.append(ProcessedFileResponse(
                    message_id=result["message_id"],
                    filename=result["filename"],
                    message_type=result["message_type"],
                    created_at=result["created_at"],
                    content_preview=result["content_preview"]
                ))
                logger.info(f"Successfully processed file: {file_info['filename']}")
                
            except Exception as e:
                error_msg = f"Failed to process {file_info['filename']}: {str(e)}"
                logger.error(error_msg)
                errors.append({
                    "filename": file_info["filename"],
                    "error": str(e)
                })
        
        return ProcessAllFilesResponse(
            processed_files=processed_files,
            total_processed=len(processed_files),
            errors=errors
        )
    
    except Exception as e:
        logger.error(f"Unexpected error processing all files: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process files: {str(e)}"
        )


@router.delete("/files/{filename}")
async def delete_file(filename: str, api_key: str = Depends(get_api_key)):
    """
    Delete a specific file from the issues directory.
    
    Args:
        filename: Name of the file to delete
        
    Returns:
        Success message
    """
    try:
        logger.info(f"Attempting to delete file: {filename}")
        
        # Get secure file path (this validates the filename)
        file_path = issues_service._get_secure_file_path(filename)
        
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File '{filename}' not found in issues directory"
            )
        
        # Delete the file
        file_path.unlink()
        logger.info(f"Successfully deleted file: {filename}")
        
        return {"message": f"File '{filename}' deleted successfully"}
    
    except ValueError as e:
        error_msg = str(e)
        if any(pattern in error_msg for pattern in [
            "Path traversal detected", "Invalid filename", 
            "Hidden files are not allowed", "Filename contains null bytes"
        ]):
            logger.warning(f"Security violation attempt - {error_msg}: {filename}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename"
            )
        else:
            logger.error(f"Error deleting file {filename}: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Unexpected error deleting file {filename}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}"
        )
