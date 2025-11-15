import pytest
import pytest_asyncio
from httpx import AsyncClient
from uuid import uuid4
from datetime import datetime

from app.main import app
from app.database import db_manager


@pytest_asyncio.fixture
async def client():
    """Create test client"""
    from fastapi.testclient import TestClient
    from httpx import ASGITransport
    async with AsyncClient(
        transport=ASGITransport(app=app), 
        base_url="http://test"
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


@pytest.mark.asyncio
async def test_create_agent(client: AsyncClient):
    """Test creating a new agent"""
    payload = {
        "agent_name": "test-agent",
        "ip_address": "192.168.1.100", 
        "port": 8080
    }
    response = await client.post("/agents", json=payload)
    assert response.status_code == 201
    
    agent_data = response.json()
    assert "id" in agent_data
    assert agent_data["agent_name"] == "test-agent"
    assert agent_data["ip_address"] == "192.168.1.100"
    assert agent_data["port"] == 8080
    assert "created_at" in agent_data


@pytest.mark.asyncio
async def test_update_agent(client: AsyncClient):
    """Test updating an existing agent"""
    # First create an agent
    create_payload = {
        "agent_name": "initial-agent",
        "ip_address": "192.168.1.100", 
        "port": 8080
    }
    create_response = await client.post("/agents", json=create_payload)
    assert create_response.status_code == 201
    agent = create_response.json()
    
    # Update the agent
    update_payload = {
        "agent_name": "updated-agent",
        "port": 9090
    }
    update_response = await client.put(f"/agents/{agent['id']}", json=update_payload)
    assert update_response.status_code == 200
    
    updated_agent = update_response.json()
    assert updated_agent["agent_name"] == "updated-agent"
    assert updated_agent["port"] == 9090
    assert updated_agent["ip_address"] == "192.168.1.100"  # Should remain unchanged


@pytest.mark.asyncio
async def test_update_nonexistent_agent(client: AsyncClient):
    """Test updating a non-existent agent returns 404"""
    fake_id = str(uuid4())
    update_payload = {"agent_name": "fake-agent"}
    
    response = await client.put(f"/agents/{fake_id}", json=update_payload)
    assert response.status_code == 404
    assert "Agent not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_message(client: AsyncClient):
    """Test creating a new message"""
    # First create an agent as sender
    agent_payload = {
        "agent_name": "sender-agent",
        "ip_address": "192.168.1.100",
        "port": 8080
    }
    agent_response = await client.post("/agents", json=agent_payload)
    assert agent_response.status_code == 201
    agent = agent_response.json()
    
    # Create a message
    message_payload = {
        "content": "Hello, this is a test message!",
        "sender_id": agent["id"],
        "message_type": "text",
        "importance": 5
    }
    response = await client.post("/messages", json=message_payload)
    assert response.status_code == 201
    
    message_data = response.json()
    assert "id" in message_data
    assert message_data["content"] == "Hello, this is a test message!"
    assert message_data["sender_id"] == agent["id"]
    assert message_data["message_type"] == "text"
    assert message_data["importance"] == 5
    assert "sent_at" in message_data


@pytest.mark.asyncio
async def test_update_message(client: AsyncClient):
    """Test updating an existing message"""
    # Create agent and message first
    agent_payload = {
        "agent_name": "sender-agent",
        "ip_address": "192.168.1.100",
        "port": 8080
    }
    agent_response = await client.post("/agents", json=agent_payload)
    agent = agent_response.json()
    
    message_payload = {
        "content": "Original message",
        "sender_id": agent["id"]
    }
    message_response = await client.post("/messages", json=message_payload)
    assert message_response.status_code == 201
    message = message_response.json()
    
    # Update the message
    update_payload = {
        "content": "Updated message content",
        "importance": 8
    }
    update_response = await client.put(f"/messages/{message['id']}", json=update_payload)
    assert update_response.status_code == 200
    
    updated_message = update_response.json()
    assert updated_message["content"] == "Updated message content"
    assert updated_message["importance"] == 8


@pytest.mark.asyncio
async def test_create_message_recipient(client: AsyncClient):
    """Test creating a message recipient relationship"""
    # Create sender and recipient agents
    sender_payload = {
        "agent_name": "sender-agent",
        "ip_address": "192.168.1.100",
        "port": 8080
    }
    sender_response = await client.post("/agents", json=sender_payload)
    sender = sender_response.json()
    
    recipient_payload = {
        "agent_name": "recipient-agent", 
        "ip_address": "192.168.1.101",
        "port": 8081
    }
    recipient_response = await client.post("/agents", json=recipient_payload)
    recipient = recipient_response.json()
    
    # Create a message
    message_payload = {
        "content": "Message for recipient",
        "sender_id": sender["id"]
    }
    message_response = await client.post("/messages", json=message_payload)
    message = message_response.json()
    
    # Create message recipient relationship
    recipient_payload = {
        "message_id": message["id"],
        "recipient_id": recipient["id"],
        "is_read": False
    }
    response = await client.post("/message_recipients", json=recipient_payload)
    assert response.status_code == 201
    
    recipient_data = response.json()
    assert recipient_data["message_id"] == message["id"]
    assert recipient_data["recipient_id"] == recipient["id"]
    assert recipient_data["is_read"] == False
    assert recipient_data["read_at"] is None


@pytest.mark.asyncio
async def test_update_message_recipient(client: AsyncClient):
    """Test updating a message recipient relationship"""
    # Setup agents, message, and recipient relationship
    sender_payload = {
        "agent_name": "sender-agent",
        "ip_address": "192.168.1.100",
        "port": 8080
    }
    sender_response = await client.post("/agents", json=sender_payload)
    sender = sender_response.json()
    
    recipient_payload = {
        "agent_name": "recipient-agent",
        "ip_address": "192.168.1.101", 
        "port": 8081
    }
    recipient_response = await client.post("/agents", json=recipient_payload)
    recipient = recipient_response.json()
    
    message_payload = {
        "content": "Test message",
        "sender_id": sender["id"]
    }
    message_response = await client.post("/messages", json=message_payload)
    message = message_response.json()
    
    create_recipient_payload = {
        "message_id": message["id"],
        "recipient_id": recipient["id"],
        "is_read": False
    }
    create_recipient_response = await client.post("/message_recipients", json=create_recipient_payload)
    assert create_recipient_response.status_code == 201
    
    # Update to mark as read
    update_payload = {
        "is_read": True,
        "read_at": datetime.now().isoformat()
    }
    update_response = await client.put(
        f"/message_recipients/{message['id']}/{recipient['id']}", 
        json=update_payload
    )
    assert update_response.status_code == 200
    
    updated_recipient = update_response.json()
    assert updated_recipient["is_read"] == True
    assert updated_recipient["read_at"] is not None


@pytest.mark.asyncio
async def test_create_agent_message_metadata(client: AsyncClient):
    """Test creating agent message metadata"""
    # Create agent and message
    agent_payload = {
        "agent_name": "test-agent",
        "ip_address": "192.168.1.100",
        "port": 8080
    }
    agent_response = await client.post("/agents", json=agent_payload)
    agent = agent_response.json()
    
    message_payload = {
        "content": "Test message with metadata",
        "sender_id": agent["id"]
    }
    message_response = await client.post("/messages", json=message_payload)
    message = message_response.json()
    
    # Create metadata
    metadata_payload = {
        "message_id": message["id"],
        "key": "priority",
        "value": "high"
    }
    response = await client.post("/agent_message_metadata", json=metadata_payload)
    assert response.status_code == 201
    
    metadata_data = response.json()
    assert "id" in metadata_data
    assert metadata_data["message_id"] == message["id"]
    assert metadata_data["key"] == "priority"
    assert metadata_data["value"] == "high"
    assert "created_at" in metadata_data


@pytest.mark.asyncio
async def test_update_agent_message_metadata(client: AsyncClient):
    """Test updating agent message metadata"""
    # Setup agent, message, and metadata
    agent_payload = {
        "agent_name": "test-agent",
        "ip_address": "192.168.1.100",
        "port": 8080
    }
    agent_response = await client.post("/agents", json=agent_payload)
    agent = agent_response.json()
    
    message_payload = {
        "content": "Test message",
        "sender_id": agent["id"]
    }
    message_response = await client.post("/messages", json=message_payload)
    message = message_response.json()
    
    create_metadata_payload = {
        "message_id": message["id"],
        "key": "status",
        "value": "pending"
    }
    create_metadata_response = await client.post("/agent_message_metadata", json=create_metadata_payload)
    assert create_metadata_response.status_code == 201
    metadata = create_metadata_response.json()
    
    # Update the metadata
    update_payload = {
        "value": "completed"
    }
    update_response = await client.put(f"/agent_message_metadata/{metadata['id']}", json=update_payload)
    assert update_response.status_code == 200
    
    updated_metadata = update_response.json()
    assert updated_metadata["value"] == "completed"
    assert updated_metadata["key"] == "status"


@pytest.mark.asyncio
async def test_agent_validation(client: AsyncClient):
    """Test agent validation with invalid data"""
    # Test invalid port
    invalid_payload = {
        "agent_name": "test-agent",
        "ip_address": "192.168.1.100",
        "port": 70000  # Invalid port number
    }
    response = await client.post("/agents", json=invalid_payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_message_with_conversation_thread(client: AsyncClient):
    """Test message threading and conversation functionality"""
    # Create agent
    agent_payload = {
        "agent_name": "test-agent",
        "ip_address": "192.168.1.100",
        "port": 8080
    }
    agent_response = await client.post("/agents", json=agent_payload)
    agent = agent_response.json()
    
    # Create parent message
    parent_payload = {
        "content": "Original message",
        "sender_id": agent["id"]
    }
    parent_response = await client.post("/messages", json=parent_payload)
    assert parent_response.status_code == 201
    parent_message = parent_response.json()
    
    # Create reply message
    reply_payload = {
        "content": "Reply to original message",
        "sender_id": agent["id"],
        "parent_message_id": parent_message["id"],
        "conversation_id": parent_message["conversation_id"]
    }
    reply_response = await client.post("/messages", json=reply_payload)
    assert reply_response.status_code == 201
    
    reply_message = reply_response.json()
    assert reply_message["parent_message_id"] == parent_message["id"]
    assert reply_message["conversation_id"] == parent_message["conversation_id"]