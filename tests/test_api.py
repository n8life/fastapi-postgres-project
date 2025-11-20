import pytest
import pytest_asyncio
import os
from httpx import AsyncClient
from app.main import app
from app.database import db_manager


@pytest_asyncio.fixture
async def client():
    """Create test client with API key authentication"""
    # Set up test environment
    os.environ["API_KEY"] = "test-api-key-123"
    os.environ["ENFORCE_HTTPS"] = "false"
    
    from httpx import ASGITransport
    headers = {"X-API-Key": "test-api-key-123"}
    async with AsyncClient(
        transport=ASGITransport(app=app), 
        base_url="http://test",
        headers=headers
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
async def test_root_endpoint(client: AsyncClient):
    """Test the root endpoint"""
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "FastAPI PostgreSQL Demo API"}


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    """Test the health endpoint"""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_get_user_success(client: AsyncClient):
    """Test getting a valid user"""
    response = await client.get("/users/1")
    assert response.status_code == 200
    
    user_data = response.json()
    assert "id" in user_data
    assert "name" in user_data
    assert "email" in user_data
    assert "created_at" in user_data
    assert user_data["id"] == 1


@pytest.mark.asyncio
async def test_get_user_not_found(client: AsyncClient):
    """Test getting a non-existent user"""
    response = await client.get("/users/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}


@pytest.mark.asyncio
async def test_user_response_structure(client: AsyncClient):
    """Test that user response has correct structure"""
    response = await client.get("/users/1")
    assert response.status_code == 200
    
    user_data = response.json()
    required_fields = ["id", "name", "email", "created_at"]
    
    for field in required_fields:
        assert field in user_data, f"Missing field: {field}"
    
    assert isinstance(user_data["id"], int)
    assert isinstance(user_data["name"], str)
    assert isinstance(user_data["email"], str)
    assert isinstance(user_data["created_at"], str)