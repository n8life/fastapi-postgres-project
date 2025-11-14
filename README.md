# FastAPI PostgreSQL Demo

A simple FastAPI application that connects to a PostgreSQL database and provides a REST API to read user records.

## Features

- FastAPI web framework with async support
- PostgreSQL database integration using asyncpg
- Docker and Docker Compose setup for easy deployment
- Comprehensive test suite
- Environment-based configuration
- Database connection pooling
- Health check endpoint

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application
│   └── database.py      # Database connection and queries
├── tests/
│   ├── __init__.py
│   └── test_api.py      # API endpoint tests
├── docker-compose.yml   # Docker services configuration
├── Dockerfile          # FastAPI app container
├── pyproject.toml      # Project dependencies (uv)
├── uv.lock            # Lock file
└── README.md
```

## API Endpoints

### Core Endpoints
- `GET /` - Root endpoint with welcome message
- `GET /health` - Health check endpoint
- `GET /users/{user_id}` - Get user by ID from database

### Messages and Agents API

The application provides a comprehensive messaging system with the following entities:

#### Database Schema Overview
- **agents**: Store agent information (UUID, name, IP address, port)
- **messages**: Main messages table with threading and conversation support
- **message_recipients**: Track message delivery and read status (composite key)
- **agent_message_metadata**: Additional key-value metadata for messages

#### Agent Management
- `POST /agents` - Create a new agent
- `PUT /agents/{agent_id}` - Update an existing agent

#### Message Management  
- `POST /messages` - Create a new message
- `PUT /messages/{message_id}` - Update an existing message

#### Message Recipients
- `POST /message_recipients` - Create a message recipient relationship
- `PUT /message_recipients/{message_id}/{recipient_id}` - Update recipient status

#### Message Metadata
- `POST /agent_message_metadata` - Add metadata to a message
- `PUT /agent_message_metadata/{metadata_id}` - Update message metadata

#### API Examples

**Create an Agent:**
```bash
curl -X POST http://localhost:8000/agents \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "ChatBot-1",
    "ip_address": "192.168.1.100",
    "port": 8080
  }'
```

**Create a Message:**
```bash
curl -X POST http://localhost:8000/messages \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Hello, this is a test message!",
    "sender_id": "agent-uuid-here",
    "message_type": "text",
    "importance": 5
  }'
```

**Message Threading:**
Messages support threading via `parent_message_id` and conversation grouping via `conversation_id`.

**Status Codes:**
- `201` - Resource created successfully
- `200` - Resource updated successfully
- `404` - Resource not found
- `409` - Constraint violation (duplicate keys, invalid references)
- `422` - Validation error (invalid data format)

## Quick Start with Docker

1. **Clone and navigate to the project:**
   ```bash
   cd /Users/nsmith/fastapi-postgres-project
   ```

2. **Start the application:**
   ```bash
   docker-compose up --build
   ```

3. **Access the API:**
   - API: http://localhost:8000
   - Interactive docs: http://localhost:8000/docs
   - ReDoc docs: http://localhost:8000/redoc

4. **Test the endpoints:**
   ```bash
   # Root endpoint
   curl http://localhost:8000/
   
   # Health check
   curl http://localhost:8000/health
   
   # Get user by ID
   curl http://localhost:8000/users/1
   ```

## Local Development Setup

### Prerequisites

- Python 3.11+
- uv package manager
- Docker and Docker Compose (for database)

### Setup Steps

1. **Install dependencies:**
   ```bash
   uv sync
   ```

2. **Start PostgreSQL database:**
   ```bash
   docker-compose up db -d
   ```

3. **Set environment variables:**
   ```bash
   export DATABASE_URL="postgresql://postgres:password@localhost:5432/testdb"
   ```

4. **Run the application:**
   ```bash
   uv run uvicorn app.main:app --reload
   ```

   Or:
   ```bash
   uv run python main.py
   ```

## Testing

Run the test suite:

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_api.py
```

## Database

The application automatically:
- Creates a `users` table on startup
- Inserts sample data if the table is empty
- Uses connection pooling for efficient database access

### Sample Data

The application creates these sample users:
- ID 1: John Doe (john@example.com)
- ID 2: Jane Smith (jane@example.com)
- ID 3: Bob Johnson (bob@example.com)

## Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
  - Default: `postgresql://postgres:password@localhost:5432/testdb`

## Security Features

- Environment-based database credentials
- Connection pooling to prevent connection exhaustion
- Input validation with Pydantic models
- Proper error handling and HTTP status codes

## Development

### Adding New Endpoints

1. Add new route functions to `app/main.py`
2. Add corresponding database functions to `app/database.py`
3. Create tests in `tests/test_api.py`

### Database Migrations

For production use, consider adding a proper migration system like Alembic.

## Deployment

The application is containerized and ready for deployment:

```bash
# Build and run with Docker Compose
docker-compose up --build -d

# Scale the application
docker-compose up --scale app=3
```

## License

MIT License