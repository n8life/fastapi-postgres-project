"""
Service module for handling issues files from the issues directory.
"""
import json
import csv
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..database import db_manager
from ..models.messaging import Message, Conversation, Agent, MessageRecipient
from sqlalchemy import select, func


class IssuesService:
    """Service for processing issues files and creating message records."""
    
    def __init__(self):
        self.issues_dir = Path(__file__).parent.parent.parent / "issues"
        # Resolve to absolute path for security checks
        self.issues_dir = self.issues_dir.resolve()
    
    def _validate_filename(self, filename: str) -> str:
        """
        Validate and sanitize filename to prevent path traversal attacks.
        
        Args:
            filename: The filename to validate
            
        Returns:
            str: The sanitized filename
            
        Raises:
            ValueError: If filename contains invalid characters or path traversal attempts
        """
        if not filename or not isinstance(filename, str):
            raise ValueError("Filename must be a non-empty string")
        
        # Remove any path separators and normalize
        clean_filename = os.path.basename(filename.strip())
        
        # Check for empty filename after cleaning
        if not clean_filename or clean_filename in ('.', '..'):
            raise ValueError("Invalid filename")
        
        # Check for null bytes and other dangerous characters
        if '\x00' in clean_filename:
            raise ValueError("Filename contains null bytes")
        
        # Additional security: ensure filename doesn't start with dots (hidden files)
        if clean_filename.startswith('.'):
            raise ValueError("Hidden files are not allowed")
        
        return clean_filename
    
    def _get_secure_file_path(self, filename: str) -> Path:
        """
        Get a secure file path within the issues directory.
        
        Args:
            filename: The filename to get path for
            
        Returns:
            Path: The secure file path
            
        Raises:
            ValueError: If path traversal is detected
        """
        clean_filename = self._validate_filename(filename)
        file_path = (self.issues_dir / clean_filename).resolve()
        
        # Ensure the resolved path is still within the issues directory
        try:
            file_path.relative_to(self.issues_dir)
        except ValueError:
            raise ValueError(f"Path traversal detected: {filename}")
        
        return file_path
    
    def get_issues_files(self) -> List[Dict[str, Any]]:
        """Get list of files in the issues directory with metadata."""
        if not self.issues_dir.exists():
            return []
        
        files = []
        for file_path in self.issues_dir.iterdir():
            if file_path.is_file() and not file_path.name.startswith('.'):
                stat_info = file_path.stat()
                files.append({
                    "filename": file_path.name,
                    "file_path": str(file_path),
                    "size": stat_info.st_size,
                    "modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                    "file_type": self._get_file_type(file_path.name)
                })
        return files
    
    def _get_file_type(self, filename: str) -> str:
        """Determine file type based on extension."""
        if filename.endswith('.csv'):
            return 'csv'
        elif filename.endswith('.sarif'):
            return 'sarif'
        elif filename.endswith('.json'):
            return 'json'
        else:
            return 'unknown'
    
    def read_file_content(self, filename: str) -> Dict[str, Any]:
        """Read and parse content from a specific file."""
        # Use secure path validation
        file_path = self._get_secure_file_path(filename)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File {filename} not found in issues directory")
        
        file_type = self._get_file_type(filename)
        
        try:
            if file_type == 'csv':
                return self._read_csv_file(file_path)
            elif file_type in ['sarif', 'json']:
                return self._read_json_file(file_path)
            else:
                return self._read_text_file(file_path)
        except Exception as e:
            raise ValueError(f"Error reading file {filename}: {str(e)}")
    
    def _read_csv_file(self, file_path: Path) -> Dict[str, Any]:
        """Read and parse CSV file."""
        rows = []
        with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                rows.append(row)
        
        return {
            "file_type": "csv",
            "filename": file_path.name,
            "row_count": len(rows),
            "columns": list(rows[0].keys()) if rows else [],
            "data": rows
        }
    
    def _read_json_file(self, file_path: Path) -> Dict[str, Any]:
        """Read and parse JSON/SARIF file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if it's actually a JSON file or just contains JSON data
        try:
            json_data = json.loads(content)
            return {
                "file_type": "json",
                "filename": file_path.name,
                "content": json_data,
                "raw_content": content
            }
        except json.JSONDecodeError:
            # If not valid JSON, treat as text with potential JSON content
            return {
                "file_type": "text_with_json",
                "filename": file_path.name,
                "raw_content": content,
                "content": self._extract_json_from_text(content)
            }
    
    def _read_text_file(self, file_path: Path) -> Dict[str, Any]:
        """Read text file content."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            "file_type": "text",
            "filename": file_path.name,
            "content": content,
            "line_count": len(content.splitlines())
        }
    
    def _extract_json_from_text(self, content: str) -> Optional[Dict[str, Any]]:
        """Try to extract JSON from text content."""
        # Look for JSON content after HTTP headers
        lines = content.split('\n')
        json_start = -1
        
        for i, line in enumerate(lines):
            if line.strip().startswith('{'):
                json_start = i
                break
        
        if json_start >= 0:
            json_content = '\n'.join(lines[json_start:])
            try:
                return json.loads(json_content)
            except json.JSONDecodeError:
                return None
        
        return None
    
    async def create_message_from_file(self, filename: str) -> Dict[str, Any]:
        """Create a message record from a file in the issues directory."""
        # Validate filename first for early error detection
        clean_filename = self._validate_filename(filename)
        
        # Read file content (this will also validate the path)
        file_data = self.read_file_content(clean_filename)
        
        # Create or get agent for system/issues processing
        agent = await self._get_or_create_issues_agent()
        
        # Create or get conversation for issues
        conversation = await self._get_or_create_issues_conversation()
        
        # Create message content
        message_content = self._format_message_content(file_data)
        
        # Create message record
        async with db_manager.get_connection() as session:
            message = Message(
                sender_id=agent.id,
                conversation_id=conversation.id,
                content=message_content,
                message_type="issues_file",
                importance=5,
                status="processed",
                msg_metadata={
                    "source_file": filename,
                    "file_type": file_data.get("file_type"),
                    "processed_at": datetime.utcnow().isoformat(),
                    "original_data": file_data
                }
            )
            
            session.add(message)
            await session.commit()
            await session.refresh(message)
            
            return {
                "message_id": str(message.id),
                "filename": filename,
                "message_type": message.message_type,
                "created_at": message.sent_at.isoformat() if message.sent_at else None,
                "content_preview": message_content[:200] + "..." if len(message_content) > 200 else message_content
            }
    
    async def _get_or_create_issues_agent(self) -> Agent:
        """Get or create the system agent for issues processing."""
        async with db_manager.get_connection() as session:
            from sqlalchemy import select
            
            # Try to find existing issues agent
            result = await session.execute(
                select(Agent).where(Agent.agent_name == "issues_processor")
            )
            agent = result.scalar_one_or_none()
            
            if not agent:
                agent = Agent(
                    agent_name="issues_processor",
                    ip_address=None,
                    port=None
                )
                session.add(agent)
                await session.commit()
                await session.refresh(agent)
            
            return agent
    
    async def _get_or_create_issues_conversation(self) -> Conversation:
        """Get or create the conversation for issues processing."""
        async with db_manager.get_connection() as session:
            from sqlalchemy import select
            
            # Try to find existing issues conversation
            result = await session.execute(
                select(Conversation).where(Conversation.title == "Issues Processing")
            )
            conversation = result.scalar_one_or_none()
            
            if not conversation:
                conversation = Conversation(
                    title="Issues Processing",
                    description="Automated processing of files from issues directory",
                    archived=False,
                    conv_metadata={
                        "purpose": "issues_processing",
                        "created_by": "system"
                    }
                )
                session.add(conversation)
                await session.commit()
                await session.refresh(conversation)
            
            return conversation
    
    def get_most_recent_file(self) -> Optional[Dict[str, Any]]:
        """Get the most recent file from the issues directory based on modification time."""
        if not self.issues_dir.exists():
            return None
        
        most_recent_file = None
        most_recent_time = 0
        
        for file_path in self.issues_dir.iterdir():
            if file_path.is_file() and not file_path.name.startswith('.'):
                stat_info = file_path.stat()
                if stat_info.st_mtime > most_recent_time:
                    most_recent_time = stat_info.st_mtime
                    most_recent_file = {
                        "filename": file_path.name,
                        "file_path": str(file_path),
                        "size": stat_info.st_size,
                        "modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                        "file_type": self._get_file_type(file_path.name)
                    }
        
        return most_recent_file
    
    async def _get_agent_by_name(self, agent_name: str) -> Optional[Agent]:
        """Get agent by agent name."""
        async with db_manager.get_connection() as session:
            result = await session.execute(
                select(Agent).where(Agent.agent_name == agent_name)
            )
            return result.scalar_one_or_none()
    
    async def _get_current_agent(self) -> Agent:
        """Get the current agent based on AGENT_NAME environment variable."""
        agent_name = os.getenv("AGENT_NAME", "task_assigner")
        
        # Try to find existing agent
        agent = await self._get_agent_by_name(agent_name)
        
        if not agent:
            # Create the agent if it doesn't exist
            async with db_manager.get_connection() as session:
                agent = Agent(
                    agent_name=agent_name,
                    ip_address=None,
                    port=None
                )
                session.add(agent)
                await session.commit()
                await session.refresh(agent)
        
        return agent
    
    async def _get_recipient_agent(self, exclude_agent_id: str) -> Optional[Agent]:
        """Get an agent to assign as recipient, excluding the sender agent."""
        async with db_manager.get_connection() as session:
            result = await session.execute(
                select(Agent).where(Agent.id != exclude_agent_id)
            )
            agents = result.scalars().all()
            
            # Return the first available agent that's not the sender
            if agents:
                return agents[0]
            
            # If no other agents exist, create a default recipient agent
            recipient_agent = Agent(
                agent_name="default_recipient",
                ip_address=None,
                port=None
            )
            session.add(recipient_agent)
            await session.commit()
            await session.refresh(recipient_agent)
            return recipient_agent
    
    async def assign_task_from_recent_file(self) -> Dict[str, Any]:
        """Assign a task from the most recent file to an agent."""
        # Get the most recent file
        recent_file = self.get_most_recent_file()
        if not recent_file:
            raise FileNotFoundError("No files found in issues directory")
        
        filename = recent_file["filename"]
        
        # Read file content
        file_data = self.read_file_content(filename)
        
        # Get current agent (sender)
        sender_agent = await self._get_current_agent()
        
        # Get recipient agent (different from sender)
        recipient_agent = await self._get_recipient_agent(sender_agent.id)
        
        if not recipient_agent:
            raise ValueError("Unable to find or create recipient agent")
        
        # Create a new conversation for this task
        conversation = await self._create_task_conversation(filename)
        
        # Create message content
        message_content = self._format_message_content(file_data)
        
        # Create message record with recipient assignment
        async with db_manager.get_connection() as session:
            # Create the message
            message = Message(
                sender_id=sender_agent.id,
                conversation_id=conversation.id,
                content=message_content,
                message_type="task_assignment",
                importance=7,
                status="assigned",
                msg_metadata={
                    "source_file": filename,
                    "file_type": file_data.get("file_type"),
                    "processed_at": datetime.utcnow().isoformat(),
                    "assigned_to": str(recipient_agent.id),
                    "original_data": file_data
                }
            )
            
            session.add(message)
            await session.commit()
            await session.refresh(message)
            
            # Create message recipient relationship
            message_recipient = MessageRecipient(
                message_id=message.id,
                recipient_id=recipient_agent.id,
                is_read=False
            )
            
            session.add(message_recipient)
            await session.commit()
            
            # Delete the processed file
            file_deleted = False
            try:
                file_path = self._get_secure_file_path(filename)
                file_path.unlink()
                file_deleted = True
            except Exception as e:
                # Log error but don't fail the entire operation
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to delete file {filename}: {str(e)}")
            
            return {
                "message_id": str(message.id),
                "conversation_id": str(conversation.id),
                "filename": filename,
                "sender_agent": sender_agent.agent_name,
                "recipient_agent": recipient_agent.agent_name,
                "message_type": message.message_type,
                "created_at": message.sent_at.isoformat() if message.sent_at else None,
                "content_preview": message_content[:200] + "..." if len(message_content) > 200 else message_content,
                "file_deleted": file_deleted
            }
    
    async def _create_task_conversation(self, filename: str) -> Conversation:
        """Create a new conversation for a task assignment."""
        async with db_manager.get_connection() as session:
            conversation = Conversation(
                title=f"Task Assignment: {filename}",
                description=f"Task assignment created from processing file: {filename}",
                archived=False,
                conv_metadata={
                    "purpose": "task_assignment",
                    "source_file": filename,
                    "created_by": "system",
                    "created_at": datetime.utcnow().isoformat()
                }
            )
            session.add(conversation)
            await session.commit()
            await session.refresh(conversation)
            return conversation
    
    def _format_message_content(self, file_data: Dict[str, Any]) -> str:
        """Format file data into a readable message content."""
        filename = file_data.get("filename", "unknown")
        file_type = file_data.get("file_type", "unknown")
        
        content_parts = [
            f"Processed file: {filename}",
            f"File type: {file_type}",
            ""
        ]
        
        if file_type == "csv":
            row_count = file_data.get("row_count", 0)
            columns = file_data.get("columns", [])
            content_parts.extend([
                f"CSV file with {row_count} rows",
                f"Columns: {', '.join(columns)}",
                ""
            ])
            
            # Add sample of first few rows
            data = file_data.get("data", [])
            if data:
                content_parts.append("Sample data:")
                for i, row in enumerate(data[:3]):  # First 3 rows
                    content_parts.append(f"Row {i+1}: {dict(row)}")
                
                if len(data) > 3:
                    content_parts.append(f"... and {len(data) - 3} more rows")
        
        elif file_type in ["json", "text_with_json"]:
            content = file_data.get("content")
            if content:
                content_parts.extend([
                    "JSON content summary:",
                    f"Keys: {', '.join(content.keys()) if isinstance(content, dict) else 'Not a dictionary'}",
                    ""
                ])
                
                # Add specific processing for issues data
                if isinstance(content, dict) and "issues" in content:
                    issues = content["issues"]
                    if isinstance(issues, list):
                        content_parts.extend([
                            f"Found {len(issues)} security issues:",
                            ""
                        ])
                        
                        for i, issue in enumerate(issues[:3]):  # First 3 issues
                            if isinstance(issue, dict):
                                title = issue.get("title", "Unknown")
                                severity = issue.get("severityCode", "Unknown")
                                content_parts.append(f"Issue {i+1}: {title} (Severity: {severity})")
                        
                        if len(issues) > 3:
                            content_parts.append(f"... and {len(issues) - 3} more issues")
        
        else:
            # For text files
            raw_content = file_data.get("content", "")
            if raw_content:
                lines = raw_content.splitlines()
                content_parts.extend([
                    f"Text file with {len(lines)} lines",
                    "Content preview:",
                    raw_content[:500] + "..." if len(raw_content) > 500 else raw_content
                ])
        
        return "\n".join(content_parts)


# Create service instance
issues_service = IssuesService()