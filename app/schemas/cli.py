from pydantic import BaseModel, Field, field_validator
from typing import Optional
import re


class EchoRequest(BaseModel):
    """Request model for echoing a message to command line"""
    message: str = Field(
        ..., 
        description="Message to echo to command line",
        min_length=1,
        max_length=1000
    )
    
    @field_validator('message')
    @classmethod
    def validate_message_content(cls, v):
        """Ensure message contains only safe characters"""
        # Allow alphanumeric, spaces, basic punctuation, but no shell metacharacters
        if not re.match(r'^[a-zA-Z0-9\s\.\,\!\?\-_]+$', v):
            raise ValueError(
                'Message contains invalid characters. Only alphanumeric characters, '
                'spaces, and basic punctuation (.,!?-_) are allowed.'
            )
        return v.strip()


class EchoResponse(BaseModel):
    """Response model for echo command execution"""
    success: bool = Field(..., description="Whether the echo command was successful")
    message: str = Field(..., description="The original message that was echoed")
    output: Optional[str] = Field(None, description="Command output if available")
    error: Optional[str] = Field(None, description="Error message if command failed")