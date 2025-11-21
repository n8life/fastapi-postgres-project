"""
Pydantic schemas for issues endpoints.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class IssueFileInfo(BaseModel):
    """Information about a file in the issues directory."""
    filename: str = Field(..., description="Name of the file")
    file_path: str = Field(..., description="Full path to the file")
    size: int = Field(..., description="File size in bytes")
    modified: str = Field(..., description="Last modified timestamp (ISO format)")
    file_type: str = Field(..., description="Type of file (csv, sarif, json, unknown)")


class IssueFilesResponse(BaseModel):
    """Response containing list of files in issues directory."""
    files: List[IssueFileInfo] = Field(..., description="List of files in issues directory")
    total_count: int = Field(..., description="Total number of files")


class ProcessFileRequest(BaseModel):
    """Request to process a specific file and create a message."""
    filename: str = Field(..., description="Name of the file to process")


class ProcessedFileResponse(BaseModel):
    """Response after processing a file and creating a message."""
    message_id: str = Field(..., description="ID of the created message")
    filename: str = Field(..., description="Name of the processed file")
    message_type: str = Field(..., description="Type of the created message")
    created_at: Optional[str] = Field(None, description="Message creation timestamp (ISO format)")
    content_preview: str = Field(..., description="Preview of the message content")


class FileContentResponse(BaseModel):
    """Response containing the content of a specific file."""
    filename: str = Field(..., description="Name of the file")
    file_type: str = Field(..., description="Type of file")
    content: Dict[str, Any] = Field(..., description="Parsed content of the file")


class CSVFileContent(BaseModel):
    """Specific schema for CSV file content."""
    file_type: str = Field("csv", description="File type")
    filename: str = Field(..., description="Name of the file")
    row_count: int = Field(..., description="Number of rows in CSV")
    columns: List[str] = Field(..., description="Column names")
    data: List[Dict[str, Any]] = Field(..., description="CSV data as list of dictionaries")


class JSONFileContent(BaseModel):
    """Specific schema for JSON/SARIF file content."""
    file_type: str = Field("json", description="File type")
    filename: str = Field(..., description="Name of the file")
    content: Dict[str, Any] = Field(..., description="Parsed JSON content")
    raw_content: Optional[str] = Field(None, description="Raw file content")


class TextFileContent(BaseModel):
    """Specific schema for text file content."""
    file_type: str = Field("text", description="File type")
    filename: str = Field(..., description="Name of the file")
    content: str = Field(..., description="Text content of the file")
    line_count: int = Field(..., description="Number of lines in the file")


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")


class ProcessAllFilesResponse(BaseModel):
    """Response after processing all files in the issues directory."""
    processed_files: List[ProcessedFileResponse] = Field(..., description="List of processed files")
    total_processed: int = Field(..., description="Total number of files processed")
    errors: List[Dict[str, str]] = Field(default_factory=list, description="List of files that failed to process")