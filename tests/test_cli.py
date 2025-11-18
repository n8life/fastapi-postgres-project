import pytest
import pytest_asyncio
from httpx import AsyncClient
from unittest.mock import patch, MagicMock
import subprocess
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


@pytest.mark.asyncio
async def test_echo_endpoint_success(client: AsyncClient):
    """Test successful echo command execution"""
    test_message = "Hello World"
    
    with patch('subprocess.run') as mock_subprocess:
        # Mock successful subprocess execution
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = f"{test_message}\n"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        response = await client.post(
            "/cli/echo",
            json={"message": test_message}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["message"] == test_message
        assert data["output"] == test_message
        assert data["error"] is None
        
        # Verify subprocess was called with proper escaping
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args
        assert "echo 'Hello World'" in call_args[0][0]
        assert call_args[1]["shell"] is True
        assert call_args[1]["capture_output"] is True
        assert call_args[1]["text"] is True
        assert call_args[1]["timeout"] == 10


@pytest.mark.asyncio
async def test_echo_endpoint_with_special_characters(client: AsyncClient):
    """Test echo command with allowed special characters"""
    test_message = "Hello, World! How are you?"
    
    with patch('subprocess.run') as mock_subprocess:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = f"{test_message}\n"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        response = await client.post(
            "/cli/echo",
            json={"message": test_message}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == test_message


@pytest.mark.asyncio
async def test_echo_endpoint_invalid_characters(client: AsyncClient):
    """Test echo endpoint with invalid/dangerous characters"""
    dangerous_messages = [
        "Hello; rm -rf /",  # Command injection attempt
        "Hello && ls -la",   # Command chaining
        "Hello | cat /etc/passwd",  # Pipe command
        "Hello `whoami`",    # Command substitution
        "Hello $(whoami)",   # Command substitution
        "Hello & sleep 10",  # Background process
        "Hello > /tmp/test", # Output redirection
        "Hello < /etc/passwd" # Input redirection
    ]
    
    for message in dangerous_messages:
        response = await client.post(
            "/cli/echo",
            json={"message": message}
        )
        
        assert response.status_code == 422, f"Should reject dangerous message: {message}"
        error_msg = response.json()["detail"][0]["msg"].lower()
        assert "invalid characters" in error_msg or "value error" in error_msg


@pytest.mark.asyncio
async def test_echo_endpoint_empty_message(client: AsyncClient):
    """Test echo endpoint with empty message"""
    response = await client.post(
        "/cli/echo",
        json={"message": ""}
    )
    
    assert response.status_code == 422
    error_detail = response.json()["detail"]
    assert any("min_length" in str(error) for error in error_detail)


@pytest.mark.asyncio
async def test_echo_endpoint_too_long_message(client: AsyncClient):
    """Test echo endpoint with message exceeding max length"""
    long_message = "A" * 1001  # Exceeds 1000 character limit
    
    response = await client.post(
        "/cli/echo",
        json={"message": long_message}
    )
    
    assert response.status_code == 422
    error_detail = response.json()["detail"]
    assert any("max_length" in str(error) for error in error_detail)


@pytest.mark.asyncio
async def test_echo_endpoint_subprocess_failure(client: AsyncClient):
    """Test echo endpoint when subprocess fails"""
    test_message = "Hello World"
    
    with patch('subprocess.run') as mock_subprocess:
        # Mock failed subprocess execution
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Command failed"
        mock_subprocess.return_value = mock_result
        
        response = await client.post(
            "/cli/echo",
            json={"message": test_message}
        )
        
        assert response.status_code == 200  # Returns 200 but with success=False
        data = response.json()
        
        assert data["success"] is False
        assert data["message"] == test_message
        assert "Command failed with return code 1" in data["error"]
        assert data["output"] is None


@pytest.mark.asyncio
async def test_echo_endpoint_subprocess_timeout(client: AsyncClient):
    """Test echo endpoint when subprocess times out"""
    test_message = "Hello World"
    
    with patch('subprocess.run') as mock_subprocess:
        # Mock subprocess timeout
        mock_subprocess.side_effect = subprocess.TimeoutExpired(
            cmd="echo 'Hello World'", 
            timeout=10
        )
        
        response = await client.post(
            "/cli/echo",
            json={"message": test_message}
        )
        
        assert response.status_code == 408  # Request timeout
        data = response.json()
        assert data["detail"] == "Command execution timed out"


@pytest.mark.asyncio
async def test_echo_endpoint_unexpected_error(client: AsyncClient):
    """Test echo endpoint with unexpected error"""
    test_message = "Hello World"
    
    with patch('subprocess.run') as mock_subprocess:
        # Mock unexpected exception
        mock_subprocess.side_effect = RuntimeError("Unexpected error")
        
        response = await client.post(
            "/cli/echo",
            json={"message": test_message}
        )
        
        assert response.status_code == 500  # Internal server error
        data = response.json()
        assert "Internal server error" in data["detail"]


@pytest.mark.asyncio
async def test_echo_endpoint_missing_message_field(client: AsyncClient):
    """Test echo endpoint with missing message field"""
    response = await client.post(
        "/cli/echo",
        json={}
    )
    
    assert response.status_code == 422
    error_detail = response.json()["detail"]
    assert any("field required" in str(error).lower() for error in error_detail)


@pytest.mark.asyncio
async def test_echo_endpoint_invalid_json(client: AsyncClient):
    """Test echo endpoint with invalid JSON"""
    response = await client.post(
        "/cli/echo",
        data="invalid json"
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_echo_endpoint_message_whitespace_handling(client: AsyncClient):
    """Test that messages with leading/trailing whitespace are trimmed"""
    test_message = "  Hello World  "
    expected_message = "Hello World"
    
    with patch('subprocess.run') as mock_subprocess:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = f"{expected_message}\n"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        response = await client.post(
            "/cli/echo",
            json={"message": test_message}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == expected_message  # Should be trimmed


@pytest.mark.asyncio
async def test_echo_endpoint_numeric_message(client: AsyncClient):
    """Test echo endpoint with numeric characters"""
    test_message = "Test 123 456"
    
    with patch('subprocess.run') as mock_subprocess:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = f"{test_message}\n"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        response = await client.post(
            "/cli/echo",
            json={"message": test_message}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == test_message