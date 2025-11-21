"""
Service module for handling issues files from the issues directory.
"""
import os
import json
import csv
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..database import db_manager
from ..models.messaging import Message, Conversation, Agent


class IssuesService:
    """Service for processing issues files and creating message records."""
    
    def __init__(self):
        self.issues_dir = Path(__file__).parent.parent.parent / "issues"
    
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
        file_path = self.issues_dir / filename
        
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
        # Read file content
        file_data = self.read_file_content(filename)
        
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