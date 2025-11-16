import pytest
import pytest_asyncio
from httpx import AsyncClient
from uuid import uuid4
from datetime import datetime, timedelta

from app.main import app
from app.database import db_manager


@pytest_asyncio.fixture
async def client():
    """Create test client"""
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


@pytest_asyncio.fixture
async def test_conversation_data(client: AsyncClient):
    """Create test conversation, agents, and messages"""
    # Create conversation
    conversation_data = {
        "title": "Test Conversation",
        "description": "A test conversation for validation",
        "archived": False,
        "metadata": {"priority": "high", "category": "testing"}
    }
    conversation_response = await client.post("/conversations", json=conversation_data)
    conversation = conversation_response.json()
    
    # Create agents
    agent1_data = {
        "agent_name": "conversation-agent-1",
        "ip_address": "192.168.1.10",
        "port": 8080
    }
    agent1_response = await client.post("/agents", json=agent1_data)
    agent1 = agent1_response.json()
    
    agent2_data = {
        "agent_name": "conversation-agent-2", 
        "ip_address": "192.168.1.11",
        "port": 8081
    }
    agent2_response = await client.post("/agents", json=agent2_data)
    agent2 = agent2_response.json()
    
    # Create messages in conversation
    message1_data = {
        "content": "First message in conversation",
        "sender_id": agent1["id"],
        "conversation_id": conversation["id"],
        "message_type": "text",
        "importance": 5
    }
    message1_response = await client.post("/messages", json=message1_data)
    message1 = message1_response.json()
    
    message2_data = {
        "content": "Second message replying",
        "sender_id": agent2["id"], 
        "conversation_id": conversation["id"],
        "parent_message_id": message1["id"],
        "message_type": "reply",
        "importance": 3
    }
    message2_response = await client.post("/messages", json=message2_data)
    message2 = message2_response.json()
    
    # Create recipient relationships
    recipient1_data = {
        "message_id": message1["id"],
        "recipient_id": agent2["id"],
        "is_read": False
    }
    await client.post("/message_recipients", json=recipient1_data)
    
    recipient2_data = {
        "message_id": message2["id"],
        "recipient_id": agent1["id"],
        "is_read": True
    }
    await client.post("/message_recipients", json=recipient2_data)
    
    # Add some metadata
    metadata_data = {
        "message_id": message1["id"],
        "key": "urgency",
        "value": "high"
    }
    await client.post("/agent_message_metadata", json=metadata_data)
    
    return {
        "conversation": conversation,
        "agent1": agent1,
        "agent2": agent2,
        "message1": message1,
        "message2": message2
    }


@pytest.mark.asyncio
async def test_create_conversation(client: AsyncClient):
    """Test creating a new conversation"""
    conversation_data = {
        "title": "New Conversation",
        "description": "A brand new conversation",
        "archived": False,
        "metadata": {"team": "qa", "sprint": "2024-1"}
    }
    
    response = await client.post("/conversations", json=conversation_data)
    assert response.status_code == 201
    
    conversation = response.json()
    assert conversation["title"] == "New Conversation"
    assert conversation["description"] == "A brand new conversation"
    assert conversation["archived"] == False
    assert conversation["metadata"]["team"] == "qa"
    assert "id" in conversation
    assert "created_at" in conversation


@pytest.mark.asyncio
async def test_update_conversation(client: AsyncClient, test_conversation_data):
    """Test updating an existing conversation"""
    conversation_id = test_conversation_data["conversation"]["id"]
    
    update_data = {
        "title": "Updated Test Conversation",
        "archived": True,
        "metadata": {"status": "completed"}
    }
    
    response = await client.put(f"/conversations/{conversation_id}", json=update_data)
    assert response.status_code == 200
    
    updated_conversation = response.json()
    assert updated_conversation["title"] == "Updated Test Conversation"
    assert updated_conversation["archived"] == True
    assert updated_conversation["metadata"]["status"] == "completed"
    # Original description should remain
    assert updated_conversation["description"] == "A test conversation for validation"


@pytest.mark.asyncio
async def test_list_conversations(client: AsyncClient, test_conversation_data):
    """Test listing all conversations"""
    response = await client.get("/conversations")
    assert response.status_code == 200
    
    conversations = response.json()
    assert len(conversations) >= 1
    
    # Find our test conversation
    test_conv = next(
        (conv for conv in conversations if conv["id"] == test_conversation_data["conversation"]["id"]),
        None
    )
    assert test_conv is not None
    assert test_conv["title"] == "Test Conversation"


@pytest.mark.asyncio
async def test_get_conversation_by_id(client: AsyncClient, test_conversation_data):
    """Test getting a specific conversation by ID"""
    conversation_id = test_conversation_data["conversation"]["id"]
    
    response = await client.get(f"/conversations/{conversation_id}")
    assert response.status_code == 200
    
    conversation = response.json()
    assert conversation["id"] == conversation_id
    assert conversation["title"] == "Test Conversation"
    assert conversation["description"] == "A test conversation for validation"


@pytest.mark.asyncio
async def test_get_conversation_details(client: AsyncClient, test_conversation_data):
    """Test getting comprehensive conversation details"""
    conversation_id = test_conversation_data["conversation"]["id"]
    
    response = await client.get(f"/conversations/{conversation_id}/details")
    assert response.status_code == 200
    
    details = response.json()
    
    # Verify conversation info
    assert details["id"] == conversation_id
    assert details["title"] == "Test Conversation"
    assert details["total_messages"] == 2
    assert details["unread_count"] == 1  # One unread message
    
    # Verify messages
    assert len(details["messages"]) == 2
    message_contents = [msg["content"] for msg in details["messages"]]
    assert "First message in conversation" in message_contents
    assert "Second message replying" in message_contents
    
    # Verify threading - second message should reference first
    reply_message = next(
        msg for msg in details["messages"] 
        if msg["content"] == "Second message replying"
    )
    first_message = next(
        msg for msg in details["messages"] 
        if msg["content"] == "First message in conversation"
    )
    assert reply_message["parent_message_id"] == first_message["id"]
    
    # Verify unique agents
    assert len(details["unique_agents"]) == 2
    agent_names = [agent["agent_name"] for agent in details["unique_agents"]]
    assert "conversation-agent-1" in agent_names
    assert "conversation-agent-2" in agent_names


@pytest.mark.asyncio
async def test_conversation_error_handling(client: AsyncClient):
    """Test error handling for conversation endpoints"""
    fake_id = str(uuid4())
    
    # Test get non-existent conversation
    response = await client.get(f"/conversations/{fake_id}")
    assert response.status_code == 404
    assert "Conversation not found" in response.json()["detail"]
    
    # Test update non-existent conversation
    response = await client.put(f"/conversations/{fake_id}", json={"title": "Updated"})
    assert response.status_code == 404
    
    # Test get details for non-existent conversation
    response = await client.get(f"/conversations/{fake_id}/details")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_empty_conversation_details(client: AsyncClient):
    """Test conversation details when conversation has no messages"""
    # Create empty conversation
    conversation_data = {
        "title": "Empty Conversation",
        "description": "No messages here"
    }
    response = await client.post("/conversations", json=conversation_data)
    conversation = response.json()
    
    # Get details
    response = await client.get(f"/conversations/{conversation['id']}/details")
    assert response.status_code == 200
    
    details = response.json()
    assert details["total_messages"] == 0
    assert details["unread_count"] == 0
    assert len(details["messages"]) == 0
    assert len(details["unique_agents"]) == 0


@pytest.mark.asyncio
async def test_conversation_archiving(client: AsyncClient, test_conversation_data):
    """Test conversation archiving functionality"""
    conversation_id = test_conversation_data["conversation"]["id"]
    
    # Archive conversation
    response = await client.put(
        f"/conversations/{conversation_id}", 
        json={"archived": True}
    )
    assert response.status_code == 200
    
    # Verify archived status
    response = await client.get(f"/conversations/{conversation_id}")
    conversation = response.json()
    assert conversation["archived"] == True
    
    # Unarchive conversation
    response = await client.put(
        f"/conversations/{conversation_id}", 
        json={"archived": False}
    )
    assert response.status_code == 200
    
    # Verify unarchived status
    response = await client.get(f"/conversations/{conversation_id}")
    conversation = response.json()
    assert conversation["archived"] == False


@pytest.mark.asyncio
async def test_conversation_metadata_handling(client: AsyncClient):
    """Test conversation metadata operations"""
    # Create with metadata
    conversation_data = {
        "title": "Metadata Test",
        "metadata": {
            "project": "test-project",
            "priority": "high",
            "tags": ["important", "urgent"]
        }
    }
    response = await client.post("/conversations", json=conversation_data)
    conversation = response.json()
    
    assert conversation["metadata"]["project"] == "test-project"
    assert conversation["metadata"]["priority"] == "high"
    assert "important" in conversation["metadata"]["tags"]
    
    # Update metadata
    update_data = {
        "metadata": {
            "project": "updated-project",
            "status": "in-progress",
            "assignee": "test-user"
        }
    }
    response = await client.put(f"/conversations/{conversation['id']}", json=update_data)
    updated_conversation = response.json()
    
    assert updated_conversation["metadata"]["project"] == "updated-project"
    assert updated_conversation["metadata"]["status"] == "in-progress"
    assert updated_conversation["metadata"]["assignee"] == "test-user"


@pytest.mark.asyncio
async def test_conversation_ordering(client: AsyncClient):
    """Test that conversations are ordered by creation time (newest first)"""
    # Create multiple conversations with slight delays
    conversations = []
    for i in range(3):
        conv_data = {
            "title": f"Conversation {i}",
            "description": f"Test conversation number {i}"
        }
        response = await client.post("/conversations", json=conv_data)
        conversations.append(response.json())
    
    # Get all conversations
    response = await client.get("/conversations")
    all_conversations = response.json()
    
    # Find our test conversations
    our_conversations = [
        conv for conv in all_conversations 
        if conv["title"].startswith("Conversation ")
    ]
    
    # Should be ordered newest first
    assert len(our_conversations) >= 3
    titles = [conv["title"] for conv in our_conversations[:3]]
    assert "Conversation 2" in titles[0]  # Most recent first