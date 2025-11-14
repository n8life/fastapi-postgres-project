# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Development Commands

### Environment Setup
```bash
# Install dependencies using uv
uv sync

# Start only the PostgreSQL database for local development
docker-compose up db -d

# Set up environment variable for local development (SQLAlchemy async)
export DATABASE_URL="postgresql+asyncpg://postgres:password@localhost:5432/testdb"
```

### Running the Application
```bash
# Run with hot reload (recommended for development)
uv run uvicorn app.main:app --reload

# Alternative way to run the application
uv run python main.py

# Run with Docker Compose (full stack)
docker-compose up --build

# Run with Docker Compose in background
docker-compose up --build -d
```

### Testing
```bash
# Run all tests
uv run pytest

# Run tests with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_api.py

# Run specific test function
uv run pytest tests/test_api.py::test_get_user_success
```

## Architecture Overview

### Application Structure
- **`app/main.py`**: FastAPI application with route definitions, Pydantic models, and lifespan management
- **`app/database.py`**: Database connection pooling, table initialization, and data access functions
- **`main.py`**: Application entry point that imports and runs the FastAPI app
- **`tests/test_api.py`**: Comprehensive async test suite with database setup/teardown

### Key Architectural Patterns
- **Async/Await**: The entire application is built with async patterns using SQLAlchemy 2.0 async and FastAPI's async capabilities
- **Connection Pooling**: Uses SQLAlchemy async engine with connection pooling managed through a DatabaseManager singleton
- **Lifespan Management**: Database engine creation/cleanup handled via FastAPI's lifespan context manager
- **Environment-Based Configuration**: Database URL and other settings loaded from environment variables
- **ORM Integration**: SQLAlchemy 2.0 with modern type annotations and declarative models

### Database Architecture
- **Auto-initialization**: The database schema and sample data are created automatically on application startup via SQLAlchemy metadata
- **Connection Management**: Uses context managers (`db_manager.get_connection()`) for safe async session handling
- **Sample Data**: Automatically populates with 3 sample users if the table is empty
- **Schema Management**: SQLAlchemy ORM models with type annotations define database schema
- **Connection Pool Tuning**: Configurable via `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, and `SQLALCHEMY_ECHO` environment variables

### Testing Strategy
- **Async Test Framework**: Uses pytest-asyncio for async test execution
- **Test Isolation**: Each test gets a fresh database connection pool via fixtures
- **HTTP Client Testing**: Uses httpx.AsyncClient for testing API endpoints without network calls
- **Database Integration**: Tests run against a real PostgreSQL database for integration testing

### Key Dependencies
- **FastAPI**: Web framework with automatic OpenAPI documentation
- **SQLAlchemy**: Modern ORM with async support and type annotations
- **asyncpg**: High-performance async PostgreSQL driver (used by SQLAlchemy)
- **uvicorn**: ASGI server for running the FastAPI application
- **uv**: Fast Python package manager for dependency management
