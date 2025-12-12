import pytest
import pytest_asyncio
from httpx import AsyncClient
from uuid import uuid4
from datetime import datetime, timedelta

from app.main import app
from app.database import db_manager




@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """Setup and teardown database for tests"""
    # Setup
    await db_manager.create_pool()
    yield
    # Teardown
    await db_manager.close_pool()


@pytest_asyncio.fixture
async def test_data(client: AsyncClient):
    """Create test agents, messages, and recipients for testing"""
    # Create two agents
    agent1_data = {
        "agent_name": "agent-1",
        "ip_address": "192.168.1.100",
        "port": 8080
    }
    agent1_response = await client.post("/agents", json=agent1_data)
    agent1 = agent1_response.json()
    
    agent2_data = {
        "agent_name": "agent-2", 
        "ip_address": "192.168.1.101",
        "port": 8081
    }
    agent2_response = await client.post("/agents", json=agent2_data)
    agent2 = agent2_response.json()
    
    # Agent 1 sends message to Agent 2
    message1_data = {
        "content": "Hello from agent 1",
        "sender_id": agent1["id"],
        "message_type": "greeting"
    }
    message1_response = await client.post("/messages", json=message1_data)
    message1 = message1_response.json()
    
    # Agent 2 sends message to Agent 1
    message2_data = {
        "content": "Reply from agent 2", 
        "sender_id": agent2["id"],
        "message_type": "reply"
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
    metadata1_data = {
        "message_id": message1["id"],
        "key": "priority",
        "value": "high"
    }
    await client.post("/agent_message_metadata", json=metadata1_data)
    
    return {
        "agent1": agent1,
        "agent2": agent2,
        "message1": message1,
        "message2": message2
    }


@pytest.mark.asyncio
async def test_get_all_messages_for_agent(client: AsyncClient, test_data):
    """Test getting all messages by recipient_id lookup for an agent"""
    agent1_id = test_data["agent1"]["id"]
    
    response = await client.get(f"/agents/{agent1_id}/messages")
    assert response.status_code == 200
    
    messages = response.json()
    assert len(messages) == 1  # Agent1 received 1 message (from agent2)
    
    # Verify only received messages are returned
    message = messages[0]
    assert message["content"] == "Reply from agent 2"
    assert message["sender_id"] == test_data["agent2"]["id"]
    assert message["is_read"] == True  # Was marked as read in test data
    
    # Test agent2 gets their received message
    agent2_id = test_data["agent2"]["id"]
    response = await client.get(f"/agents/{agent2_id}/messages")
    assert response.status_code == 200
    
    messages = response.json()
    assert len(messages) == 1  # Agent2 received 1 message (from agent1)
    message = messages[0]
    assert message["content"] == "Hello from agent 1"
    assert message["sender_id"] == test_data["agent1"]["id"]
    assert message["is_read"] == False  # Unread message


@pytest.mark.asyncio
async def test_get_unread_messages_for_agent(client: AsyncClient, test_data):
    """Test getting only unread messages for an agent"""
    agent2_id = test_data["agent2"]["id"]
    
    response = await client.get(f"/agents/{agent2_id}/messages/unread")
    assert response.status_code == 200
    
    messages = response.json()
    assert len(messages) == 1  # Only unread message
    
    message = messages[0]
    assert message["content"] == "Hello from agent 1"
    assert message["is_read"] == False


@pytest.mark.asyncio  
async def test_get_message_metadata_with_agent_access_control(client: AsyncClient, test_data):
    """Test message metadata endpoint with access control"""
    agent1_id = test_data["agent1"]["id"]
    agent2_id = test_data["agent2"]["id"] 
    message1_id = test_data["message1"]["id"]
    
    # Agent 1 (sender) should have access
    response = await client.get(f"/messages/{message1_id}/metadata/{agent1_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["message_id"] == message1_id
    assert data["message"]["content"] == "Hello from agent 1"
    assert data["agent"]["agent_name"] == "agent-1"
    assert len(data["metadata_items"]) == 1
    assert data["metadata_items"][0]["key"] == "priority"
    
    # Agent 2 (recipient) should have access
    response = await client.get(f"/messages/{message1_id}/metadata/{agent2_id}")
    assert response.status_code == 200
    
    # Create third agent who shouldn't have access
    agent3_data = {
        "agent_name": "agent-3",
        "ip_address": "192.168.1.102",
        "port": 8082
    }
    agent3_response = await client.post("/agents", json=agent3_data)
    agent3 = agent3_response.json()
    
    # Agent 3 should be forbidden
    response = await client.get(f"/messages/{message1_id}/metadata/{agent3['id']}")
    assert response.status_code == 403
    assert "does not have access" in response.json()["detail"]


@pytest.mark.asyncio
async def test_mark_messages_as_read(client: AsyncClient, test_data):
    """Test marking messages as read up to a specific date"""
    agent2_id = test_data["agent2"]["id"]
    
    # First, verify there's an unread message
    response = await client.get(f"/agents/{agent2_id}/messages/unread")
    assert response.status_code == 200
    assert len(response.json()) == 1
    
    # Mark messages as read up to now
    mark_read_data = {
        "read_up_to_date": datetime.now().isoformat()
    }
    response = await client.put(f"/agents/{agent2_id}/messages/mark-read", json=mark_read_data)
    assert response.status_code == 200
    
    result = response.json()
    assert result["updated_count"] == 1
    assert agent2_id in result["message"]
    
    # Verify no more unread messages
    response = await client.get(f"/agents/{agent2_id}/messages/unread")
    assert response.status_code == 200
    assert len(response.json()) == 0


@pytest.mark.asyncio
async def test_agent_isolation_security(client: AsyncClient, test_data):
    """Test that agents can only access their own received messages"""
    agent1_id = test_data["agent1"]["id"]
    agent2_id = test_data["agent2"]["id"]
    
    # Agent 1 messages (should only see received messages)
    response = await client.get(f"/agents/{agent1_id}/messages")
    assert response.status_code == 200
    agent1_messages = response.json()
    
    # Agent 2 messages (should only see received messages) 
    response = await client.get(f"/agents/{agent2_id}/messages")
    assert response.status_code == 200
    agent2_messages = response.json()
    
    # Verify each agent only sees their received messages
    assert len(agent1_messages) == 1  # Agent1 received 1 message
    assert len(agent2_messages) == 1  # Agent2 received 1 message
    
    # Agent 1 should only see the message from Agent 2
    assert agent1_messages[0]["content"] == "Reply from agent 2"
    assert agent1_messages[0]["sender_id"] == agent2_id
    
    # Agent 2 should only see the message from Agent 1
    assert agent2_messages[0]["content"] == "Hello from agent 1" 
    assert agent2_messages[0]["sender_id"] == agent1_id
    
    # All messages should have read status since they're received messages
    for msg in agent1_messages:
        assert msg["is_read"] in [True, False]
    for msg in agent2_messages:
        assert msg["is_read"] in [True, False]


@pytest.mark.asyncio
async def test_nonexistent_agent_errors(client: AsyncClient):
    """Test error handling for non-existent agents"""
    fake_agent_id = str(uuid4())
    
    # Test all endpoints with non-existent agent
    response = await client.get(f"/agents/{fake_agent_id}/messages")
    assert response.status_code == 404
    assert "Agent not found" in response.json()["detail"]
    
    response = await client.get(f"/agents/{fake_agent_id}/messages/unread")
    assert response.status_code == 404
    
    mark_read_data = {"read_up_to_date": datetime.now().isoformat()}
    response = await client.put(f"/agents/{fake_agent_id}/messages/mark-read", json=mark_read_data)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_nonexistent_message_metadata_error(client: AsyncClient, test_data):
    """Test error handling for non-existent message in metadata endpoint"""
    agent1_id = test_data["agent1"]["id"]
    fake_message_id = str(uuid4())
    
    response = await client.get(f"/messages/{fake_message_id}/metadata/{agent1_id}")
    assert response.status_code == 404
    assert "Message not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_empty_message_lists(client: AsyncClient):
    """Test endpoints when agent has no messages"""
    # Create agent with no messages
    agent_data = {
        "agent_name": "empty-agent",
        "ip_address": "192.168.1.200",
        "port": 9000
    }
    response = await client.post("/agents", json=agent_data)
    agent = response.json()
    
    # Should return empty lists
    response = await client.get(f"/agents/{agent['id']}/messages")
    assert response.status_code == 200
    assert response.json() == []
    
    response = await client.get(f"/agents/{agent['id']}/messages/unread")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_mark_read_with_no_unread_messages(client: AsyncClient, test_data):
    """Test mark as read when there are no unread messages"""
    agent1_id = test_data["agent1"]["id"]  # Agent1 has read message
    
    mark_read_data = {"read_up_to_date": datetime.now().isoformat()}
    response = await client.put(f"/agents/{agent1_id}/messages/mark-read", json=mark_read_data)
    assert response.status_code == 200
    
    result = response.json()
    assert result["updated_count"] == 0  # No messages updated


@pytest.mark.asyncio
async def test_mark_read_with_future_date(client: AsyncClient, test_data):
    """Test mark as read with future date includes all messages"""
    agent2_id = test_data["agent2"]["id"]
    
    # Use future date
    future_date = (datetime.now() + timedelta(days=1)).isoformat()
    mark_read_data = {"read_up_to_date": future_date}
    
    response = await client.put(f"/agents/{agent2_id}/messages/mark-read", json=mark_read_data)
    assert response.status_code == 200
    
    result = response.json()
    assert result["updated_count"] == 1


@pytest.mark.asyncio
async def test_message_ordering(client: AsyncClient, test_data):
    """Test that messages are returned in correct order (newest first)"""
    agent1_id = test_data["agent1"]["id"]
    
    response = await client.get(f"/agents/{agent1_id}/messages")
    assert response.status_code == 200
    
    messages = response.json()
    # Should be ordered by sent_at descending (newest first)
    sent_times = [msg["sent_at"] for msg in messages if msg["sent_at"]]
    
    # Convert to datetime for comparison
    sent_datetimes = [datetime.fromisoformat(t.replace('Z', '+00:00')) for t in sent_times]
    
    # Verify descending order
    for i in range(len(sent_datetimes) - 1):
        assert sent_datetimes[i] >= sent_datetimes[i + 1]