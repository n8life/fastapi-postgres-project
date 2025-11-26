"""
Locust load test file for FastAPI PostgreSQL Demo API.

This file defines load tests for all API endpoints, organized by router.
Tests use realistic traffic patterns with appropriate weighting.

Usage:
    # Local testing (against localhost:8000)
    locust -f locustfile.py --host=http://localhost:8000
    
    # Kubernetes testing
    locust -f locustfile.py --host=http://<NODE_IP>:30080
    
    # Run without web UI
    locust -f locustfile.py --headless --users 10 --spawn-rate 2 --run-time 1m
"""

import os
import json
import random
from locust import HttpUser, task, between, TaskSet


# Get API key from environment variable
API_KEY = os.getenv("API_KEY", "************")


class CoreEndpointTasks(TaskSet):
    """Tasks for core API endpoints."""
    
    @task(10)
    def health_check(self):
        """Health check - most frequent endpoint."""
        self.client.get("/health", headers={"X-API-Key": API_KEY})
    
    @task(5)
    def root_endpoint(self):
        """Root endpoint."""
        self.client.get("/", headers={"X-API-Key": API_KEY})
    
    @task(2)
    def get_user(self):
        """Get user by ID."""
        user_id = random.randint(1, 3)
        self.client.get(f"/users/{user_id}", headers={"X-API-Key": API_KEY})


class MessagingTasks(TaskSet):
    """Tasks for messaging API endpoints."""
    
    def on_start(self):
        """Initialize with agent and conversation IDs."""
        self.agent_ids = []
        self.conversation_ids = []
        self.message_ids = []
    
    @task(3)
    def create_agent(self):
        """Create a new agent."""
        response = self.client.post(
            "/agents",
            json={
                "agent_name": f"loadtest_agent_{random.randint(1000, 9999)}",
                "ip_address": f"192.168.1.{random.randint(1, 254)}",
                "port": random.randint(8000, 9000)
            },
            headers={"X-API-Key": API_KEY}
        )
        if response.status_code == 201:
            data = response.json()
            self.agent_ids.append(data["id"])
    
    @task(5)
    def create_conversation(self):
        """Create a new conversation."""
        response = self.client.post(
            "/conversations",
            json={
                "title": f"Load Test Conversation {random.randint(1000, 9999)}",
                "description": "Automated load test conversation",
                "archived": False,
                "metadata": {"test": "true", "priority": random.choice(["low", "medium", "high"])}
            },
            headers={"X-API-Key": API_KEY}
        )
        if response.status_code == 201:
            data = response.json()
            self.conversation_ids.append(data["id"])
    
    @task(8)
    def create_message(self):
        """Create a new message."""
        if not self.agent_ids:
            return
        
        conversation_id = random.choice(self.conversation_ids) if self.conversation_ids else None
        
        response = self.client.post(
            "/messages",
            json={
                "content": f"Load test message content {random.randint(1000, 9999)}",
                "sender_id": random.choice(self.agent_ids),
                "conversation_id": conversation_id,
                "message_type": random.choice(["text", "system", "task_assignment"]),
                "importance": random.randint(1, 10),
                "status": "sent"
            },
            headers={"X-API-Key": API_KEY}
        )
        if response.status_code == 201:
            data = response.json()
            self.message_ids.append(data["id"])
    
    @task(4)
    def create_message_recipient(self):
        """Create a message recipient relationship."""
        if len(self.agent_ids) < 2 or not self.message_ids:
            return
        
        self.client.post(
            "/message_recipients",
            json={
                "message_id": random.choice(self.message_ids),
                "recipient_id": random.choice(self.agent_ids)
            },
            headers={"X-API-Key": API_KEY}
        )
    
    @task(6)
    def get_agent_messages(self):
        """Get all messages for an agent."""
        if not self.agent_ids:
            return
        
        agent_id = random.choice(self.agent_ids)
        self.client.get(
            f"/agents/{agent_id}/messages",
            headers={"X-API-Key": API_KEY}
        )
    
    @task(4)
    def get_agent_unread_messages(self):
        """Get unread messages for an agent."""
        if not self.agent_ids:
            return
        
        agent_id = random.choice(self.agent_ids)
        self.client.get(
            f"/agents/{agent_id}/messages/unread",
            headers={"X-API-Key": API_KEY}
        )
    
    @task(2)
    def mark_messages_as_read(self):
        """Mark messages as read for an agent."""
        if not self.agent_ids:
            return
        
        agent_id = random.choice(self.agent_ids)
        self.client.put(
            f"/agents/{agent_id}/messages/mark-read",
            json={"read_up_to_date": "2025-12-31T23:59:59Z"},
            headers={"X-API-Key": API_KEY}
        )
    
    @task(3)
    def list_conversations(self):
        """List all conversations."""
        self.client.get("/conversations", headers={"X-API-Key": API_KEY})
    
    @task(2)
    def get_conversation_details(self):
        """Get conversation details with messages."""
        if not self.conversation_ids:
            return
        
        conversation_id = random.choice(self.conversation_ids)
        self.client.get(
            f"/conversations/{conversation_id}/details",
            headers={"X-API-Key": API_KEY}
        )
    
    @task(1)
    def update_agent(self):
        """Update an agent."""
        if not self.agent_ids:
            return
        
        agent_id = random.choice(self.agent_ids)
        self.client.put(
            f"/agents/{agent_id}",
            json={"agent_name": f"updated_agent_{random.randint(1000, 9999)}"},
            headers={"X-API-Key": API_KEY}
        )
    
    @task(1)
    def update_conversation(self):
        """Update a conversation."""
        if not self.conversation_ids:
            return
        
        conversation_id = random.choice(self.conversation_ids)
        self.client.put(
            f"/conversations/{conversation_id}",
            json={"title": f"Updated Conversation {random.randint(1000, 9999)}"},
            headers={"X-API-Key": API_KEY}
        )


class CLITasks(TaskSet):
    """Tasks for CLI endpoints."""
    
    @task(1)
    def echo_message(self):
        """Test echo command endpoint."""
        self.client.post(
            "/cli/echo",
            json={"message": f"Load test echo {random.randint(1000, 9999)}"},
            headers={"X-API-Key": API_KEY}
        )


class IssuesTasks(TaskSet):
    """Tasks for issues file processing endpoints."""
    
    @task(5)
    def list_issues_files(self):
        """List all files in issues directory."""
        self.client.get("/issues/files", headers={"X-API-Key": API_KEY})
    
    @task(1)
    def get_file_content(self):
        """Get content of a specific file (may 404 if no files exist)."""
        # This will likely 404 but that's okay for load testing
        filename = f"test_issue_{random.randint(1, 10)}.txt"
        self.client.get(
            f"/issues/files/{filename}/content",
            headers={"X-API-Key": API_KEY},
            name="/issues/files/[filename]/content"
        )


class S3Tasks(TaskSet):
    """Tasks for S3 endpoints (optional, may fail if S3 not configured)."""
    
    @task(1)
    def list_s3_files(self):
        """List files from S3 (may fail if S3 not configured)."""
        # This endpoint may fail if S3 is not configured, which is acceptable
        self.client.get(
            "/s3/files",
            headers={"X-API-Key": API_KEY},
            catch_response=True
        )


class APIUser(HttpUser):
    """
    Locust user that simulates realistic API usage patterns.
    
    The user will spend time between requests to simulate real usage.
    Tasks are weighted to simulate realistic traffic patterns:
    - Core endpoints (health checks) are most frequent
    - Messaging operations are common
    - CLI and file operations are less frequent
    """
    
    # Wait 1-3 seconds between tasks
    wait_time = between(1, 3)
    
    # Define task weights for different endpoint groups
    tasks = {
        CoreEndpointTasks: 40,      # Core endpoints very frequent
        MessagingTasks: 35,          # Messaging operations common
        IssuesTasks: 15,             # File operations moderate
        CLITasks: 5,                 # CLI operations less frequent
        S3Tasks: 5                   # S3 operations less frequent
    }
    
    def on_start(self):
        """
        Called when a simulated user starts.
        Can be used for login or setup operations.
        """
        # Verify API is accessible
        response = self.client.get("/health", headers={"X-API-Key": API_KEY})
        if response.status_code != 200:
            print(f"Warning: Health check failed with status {response.status_code}")
