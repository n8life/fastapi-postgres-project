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
- **Security Features:**
  - API key authentication on all endpoints
  - HTTPS enforcement in production
  - Security headers middleware
  - Input validation with array size limits
  - Command injection prevention in CLI operations

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application entry point
│   ├── database.py      # Database connection and queries
│   ├── routers/
│   │   ├── messaging.py # Message and agent API routes
│   │   └── cli.py       # CLI command execution routes
│   └── schemas/
│       ├── messaging.py # Pydantic models for messaging API
│       └── cli.py       # Pydantic models for CLI operations
├── tests/
│   ├── __init__.py
│   ├── test_api.py                 # Core API endpoint tests
│   ├── test_messaging_endpoints.py # Message and agent API tests
│   ├── test_message_pulling.py     # Feature 3: Pull messages tests
│   ├── test_conversations.py       # Feature 4: Conversation tests
│   └── test_cli.py                 # Feature 5: CLI command tests
├── docker-compose.yml   # Docker services configuration
├── Dockerfile          # FastAPI app container
├── openapi.yaml        # OpenAPI 3.0.3 specification
├── pyproject.toml      # Project dependencies (uv)
├── uv.lock            # Lock file
└── README.md
```

## API Documentation

### OpenAPI Specification

This project includes a comprehensive OpenAPI 3.0.3 specification (`openapi.yaml`) that documents:

- **All API endpoints** with detailed descriptions and examples
- **Request/response schemas** with validation rules and data types
- **Security requirements** including API key authentication
- **Error responses** with proper HTTP status codes
- **Data models** for all entities (Agents, Messages, Conversations, etc.)

#### Viewing the API Documentation

- **Interactive Swagger UI**: http://localhost:8000/docs
- **ReDoc UI**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json
- **Static OpenAPI YAML**: `openapi.yaml` in project root

#### Security Features in OpenAPI Spec

- API key authentication scheme documented
- Input validation patterns and constraints
- Secure examples with redacted sensitive information
- Proper error handling documentation
- Array size limits (maxItems) specified for all array schemas

## Security

This application implements comprehensive security measures to protect against common vulnerabilities:

### Authentication
- **API Key Authentication**: All endpoints require a valid API key via `X-API-Key` header
- **Environment-based Configuration**: API keys are loaded from environment variables
- **No Hardcoded Secrets**: All sensitive information is externalized

### Transport Security
- **HTTPS Enforcement**: Production deployments automatically redirect HTTP to HTTPS
- **Security Headers**: Comprehensive security headers added to all responses:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `X-XSS-Protection: 1; mode=block`
  - `Strict-Transport-Security: max-age=31536000; includeSubDomains`
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `Content-Security-Policy: default-src 'self'`

### Input Validation
- **Array Size Limits**: All array inputs have maximum size constraints:
  - Messages: 1000 items maximum
  - Agents: 50 items maximum per conversation
  - Metadata: 100 items maximum
  - Error details: 20 items maximum
- **Command Injection Prevention**: CLI endpoints use `shlex.quote()` for safe shell escaping
- **Pydantic Validation**: Comprehensive input validation with type checking

### Configuration

Security settings can be configured via environment variables:

```bash
# Required: Set a strong API key
API_KEY="your-secure-api-key-here"

# Optional: HTTPS enforcement (default: true in production)
ENFORCE_HTTPS="true"

# Optional: API key requirement (default: true)
REQUIRE_API_KEY="true"
```

### Security Best Practices

1. **API Key Management**:
   - Use strong, randomly generated API keys
   - Rotate API keys regularly
   - Store API keys in secure environment variables
   - Never commit API keys to version control

2. **HTTPS Configuration**:
   - Always use HTTPS in production
   - Configure proper SSL/TLS certificates
   - Use HTTP only for local development

3. **Monitoring and Logging**:
   - Monitor for failed authentication attempts
   - Log security-related events
   - Implement rate limiting if needed

## API Endpoints

### Core Endpoints
- `GET /` - Root endpoint with welcome message
- `GET /health` - Health check endpoint
- `GET /users/{user_id}` - Get user by ID from database

### Messages and Agents API

The application provides a comprehensive messaging system with the following entities:

#### Database Schema Overview
- **agents**: Store agent information (UUID, name, IP address, port)
- **conversations**: Conversation organization with title, description, archived status, and metadata (Feature 4)
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

#### Message Retrieval for Agents (Feature 3)
- `GET /agents/{agent_id}/messages` - Pull all messages for an agent (sent and received)
- `GET /agents/{agent_id}/messages/unread` - Pull unread messages for an agent
- `GET /messages/{message_id}/metadata/{agent_id}` - Get message metadata with agent information
- `PUT /agents/{agent_id}/messages/mark-read` - Mark messages as read up to a given date

#### Conversation Management (Feature 4)
- `POST /conversations` - Create a new conversation
- `PUT /conversations/{conversation_id}` - Update an existing conversation
- `GET /conversations` - List all conversations (ordered by creation date, newest first)
- `GET /conversations/{conversation_id}` - Get a single conversation by ID
- `GET /conversations/{conversation_id}/details` - Get comprehensive conversation info with all messages, agents, and metadata

#### CLI Command Execution (Feature 5)
- `POST /cli/echo` - Echo a message to the command line via subprocess

#### Issues File Processing (Feature 10 & 11)
- `GET /issues/files` - List all files in the issues directory
- `GET /issues/files/{filename}/content` - Get parsed content of a specific file
- `POST /issues/process-file` - Process a specific file and create a message record
- `POST /issues/process-all` - Process all files in the issues directory
- `POST /issues/assign-task` - Assign task from most recent file to an agent (Feature 11)
- `DELETE /issues/files/{filename}` - Delete a specific file from the issues directory

#### API Examples

**Create an Agent:**
```bash
curl -X POST http://localhost:8000/agents \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{
    "agent_name": "ChatBot-1",
    "ip_address": "*************",
    "port": 8080
  }'
```

**Create a Message:**
```bash
curl -X POST http://localhost:8000/messages \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{
    "content": "Hello, this is a test message!",
    "sender_id": "agent-uuid-here",
    "message_type": "text",
    "importance": 5
  }'
```

**Pull Messages for an Agent:**
```bash
# Get all messages for an agent (sent and received)
curl -X GET http://localhost:8000/agents/{agent_id}/messages \
  -H "X-API-Key: your-api-key-here"

# Get only unread messages for an agent
curl -X GET http://localhost:8000/agents/{agent_id}/messages/unread \
  -H "X-API-Key: your-api-key-here"

# Get message metadata with agent access control
curl -X GET http://localhost:8000/messages/{message_id}/metadata/{agent_id} \
  -H "X-API-Key: your-api-key-here"

# Mark messages as read up to a specific date
curl -X PUT http://localhost:8000/agents/{agent_id}/messages/mark-read \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{"read_up_to_date": "2024-01-01T12:00:00Z"}'
```

**Create a Conversation:**
```bash
curl -X POST http://localhost:8000/conversations \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{
    "title": "Project Discussion",
    "description": "Discussion about the new features",
    "archived": false,
    "metadata": {"priority": "high", "department": "engineering"}
  }'
```

**Get Conversation Details:**
```bash
# Get comprehensive conversation information
curl -X GET http://localhost:8000/conversations/{conversation_id}/details \
  -H "X-API-Key: your-api-key-here"

# Get just conversation metadata
curl -X GET http://localhost:8000/conversations/{conversation_id} \
  -H "X-API-Key: your-api-key-here"

# List all conversations
curl -X GET http://localhost:8000/conversations \
  -H "X-API-Key: your-api-key-here"
```

**Execute CLI Commands:**
```bash
# Echo a message to the command line
curl -X POST http://localhost:8000/cli/echo \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{
    "message": "Hello from the API!"
  }'

# Response:
{
  "success": true,
  "message": "Hello from the API!",
  "output": "Hello from the API!",
  "error": null
}
```

**Task Assignment from Issues Files:**
```bash
# List all files in the issues directory
curl -X GET http://localhost:8000/issues/files \
  -H "X-API-Key: your-api-key-here"

# Process the most recent file and assign task to an agent
curl -X POST http://localhost:8000/issues/assign-task \
  -H "X-API-Key: your-api-key-here"

# Response:
{
  "message_id": "uuid-here",
  "conversation_id": "uuid-here",
  "filename": "issue-file.txt",
  "sender_agent": "task_assigner",
  "recipient_agent": "agent-name",
  "message_type": "task_assignment",
  "created_at": "2025-11-22T03:38:53.222169+00:00",
  "content_preview": "Processed file: issue-file.txt...",
  "file_deleted": true
}
```

**Message Threading and Conversations:**
Messages support threading via `parent_message_id` and conversation grouping via `conversation_id`. The conversation system (Feature 4) allows organizing related messages into structured conversations with titles, descriptions, and metadata.

**Status Codes:**
- `201` - Resource created successfully
- `200` - Resource updated successfully
- `404` - Resource not found
- `409` - Constraint violation (duplicate keys, invalid references)
- `422` - Validation error (invalid data format)

## Quick Start with Docker

1. **Clone and navigate to the project:**
   ```bash
   cd fastapi-postgres-project
   ```

2. **Start the application:**
   ```bash
   docker-compose up --build
   ```

3. **Access the API:**
   - API: http://localhost:8000
   - Interactive docs: http://localhost:8000/docs
   - ReDoc docs: http://localhost:8000/redoc
   - OpenAPI specification: `openapi.yaml` (comprehensive API documentation)

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
   export DATABASE_URL="postgresql+asyncpg://postgres:password@localhost:5432/testdb"
   ```

4. **Run the application:**
   ```bash
   uv run uvicorn app.main:app --reload
   ```

   Or:
   ```bash
   uv run python main.py
   ```

## SSH Database Connection Setup

To use SSH tunnel connection for enhanced security:

### Prerequisites
- SSH access to a server with PostgreSQL access
- SSH private key file
- PostgreSQL server accessible from the SSH server

### Local Development with SSH

1. **Set SSH environment variables:**
   ```bash
   export USE_SSH_CONNECTION=true
   export SSH_HOST=your-ssh-server.com
   export SSH_USER=your-ssh-username
   export SSH_KEY_PATH=/path/to/your/ssh/private/key
   export SSH_POSTGRES_HOST=localhost  # PostgreSQL host from SSH server perspective
   export SSH_POSTGRES_PORT=5432
   export SSH_POSTGRES_USER=postgres
   export SSH_POSTGRES_PASSWORD=your-postgres-password
   export SSH_POSTGRES_DB=your-database-name
   ```

2. **Run the application:**
   ```bash
   uv run uvicorn app.main:app --reload
   ```

### Docker with SSH Connection

1. **Create SSH docker-compose override:**
   ```bash
   # Use the provided docker-compose.ssh.yml
   docker-compose -f docker-compose.yml -f docker-compose.ssh.yml up --build
   ```

2. **Or manually set environment variables:**
   ```yaml
   services:
     app:
       environment:
         - USE_SSH_CONNECTION=true
         - SSH_HOST=your-ssh-server.com
         - SSH_USER=your-ssh-username
         - SSH_KEY_PATH=/ssh/private_key
         - SSH_POSTGRES_HOST=localhost
         - SSH_POSTGRES_PORT=5432
         - SSH_POSTGRES_USER=postgres
         - SSH_POSTGRES_PASSWORD=your-password
         - SSH_POSTGRES_DB=your-database
       volumes:
         - /path/to/your/ssh/key:/ssh/private_key:ro
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
- Creates database tables (`users`, `agents`, `messages`, `conversations`, `message_recipients`, `agent_message_metadata`) on startup
- Inserts sample data if tables are empty
- Uses connection pooling for efficient database access

### Sample Data

The application creates these sample users:
- ID 1: John Doe (john@example.com)
- ID 2: Jane Smith (jane@example.com)
- ID 3: Bob Johnson (bob@example.com)

## Database Connection Options

The application supports two database connection methods:

### Direct Connection (Default)
Connects directly to a PostgreSQL database.

### SSH Tunnel Connection
Connects to a PostgreSQL database through an SSH tunnel for enhanced security.

## Environment Variables

### Direct Connection
- `DATABASE_URL`: PostgreSQL connection string (uses asyncpg driver)
  - Default: `postgresql+asyncpg://postgres:password@localhost:5432/testdb`

### SSH Connection
- `USE_SSH_CONNECTION`: Enable SSH tunnel connection (`true`/`false`)
  - Default: `false`
- `SSH_HOST`: SSH server hostname or IP address
- `SSH_USER`: SSH username
- `SSH_KEY_PATH`: Path to SSH private key file
- `SSH_POSTGRES_HOST`: PostgreSQL host accessible from SSH server
  - Default: `localhost`
- `SSH_POSTGRES_PORT`: PostgreSQL port on SSH server
  - Default: `5432`
- `SSH_POSTGRES_USER`: PostgreSQL username
  - Default: `postgres`
- `SSH_POSTGRES_PASSWORD`: PostgreSQL password
  - Default: `postgres`
- `SSH_POSTGRES_DB`: PostgreSQL database name
  - Default: `testdb`

### Other Configuration
- `DB_POOL_SIZE`: Database connection pool size (default: 5)
- `DB_MAX_OVERFLOW`: Maximum connection pool overflow (default: 10)
- `SQLALCHEMY_ECHO`: Enable SQL query logging (`1`/`0`, default: 0)
- `AGENT_NAME`: Name of the agent for task assignments (default: `task_assigner`)

## Security Features

### Database Security
- Environment-based database credentials
- Connection pooling to prevent connection exhaustion
- **SSH Tunnel Support**: Secure database connections through encrypted SSH tunnels
- **Dual Connection Modes**: Direct or SSH-tunneled connections based on environment configuration

### API Security
- Input validation with Pydantic models
- Proper error handling and HTTP status codes
- **Agent isolation**: Agents can only access their own messages (sender/recipient)
- **Access control**: Message metadata endpoints verify agent access permissions
- **Data privacy**: No endpoint allows accessing multiple agents' information simultaneously
- **CLI security**: Command injection prevention through strict input validation and safe shell escaping
- **Command restrictions**: Only safe alphanumeric characters and basic punctuation allowed in CLI commands

### SSH Connection Security
- **Private Key Authentication**: Uses SSH private keys for secure authentication
- **Encrypted Tunnels**: All database traffic encrypted through SSH tunnel
- **No Direct Database Exposure**: PostgreSQL server doesn't need direct internet access
- **Key File Protection**: SSH keys mounted read-only in containers
- **Connection Validation**: SSH tunnel health monitoring and automatic reconnection

### Docker Security

The Docker container follows security best practices:

- **Non-root user**: Application runs as `appuser` (uid/gid 1000) instead of root
- **Health monitoring**: Built-in healthcheck using `/health` endpoint with 30-second intervals
- **Minimal permissions**: Proper file ownership and permissions for application files
- **Clean environment**: Apt cache cleanup to reduce attack surface
- **Secure defaults**: No unnecessary privileges or capabilities

## Development

### Adding New Endpoints

1. Add new route functions to `app/main.py`
2. Add corresponding database functions to `app/database.py`
3. Create tests in `tests/test_api.py`

### Database Migrations

For production use, consider adding a proper migration system like Alembic.

## Deployment

The application is containerized and ready for deployment with built-in health monitoring.

### Docker Compose

```bash
# Build and run with Docker Compose
docker-compose up --build -d

# Check container health status
docker-compose ps

# Scale the application
docker-compose up --scale app=3
```

### Kubernetes

The application includes Kubernetes manifests for production deployment. See [k8s/README.md](k8s/README.md) for detailed instructions.

Quick start:

```bash
# Set required environment variables
export POSTGRES_USER="postgres"
export POSTGRES_PASSWORD="your-secure-password"
export POSTGRES_DB="testdb"
export API_KEY="your-secure-api-key"

# Build the image
docker build -t fastapi-postgres:latest .

# Deploy to Kubernetes
kubectl apply -f k8s/namespace.yaml
kubectl create secret generic postgres-secret \
  --from-literal=POSTGRES_USER=$POSTGRES_USER \
  --from-literal=POSTGRES_PASSWORD=$POSTGRES_PASSWORD \
  --from-literal=POSTGRES_DB=$POSTGRES_DB \
  -n fastapi-postgres
kubectl create secret generic api-secret \
  --from-literal=API_KEY=$API_KEY \
  -n fastapi-postgres
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/storage.yaml
kubectl apply -f k8s/postgres-deployment.yaml
kubectl apply -f k8s/api-deployment.yaml
kubectl apply -f k8s/network-policies.yaml
```

### Health Monitoring

The Docker container includes a built-in healthcheck that:
- Tests the `/health` endpoint every 30 seconds
- Allows 10 seconds timeout per check
- Waits 5 seconds before starting checks
- Marks container unhealthy after 3 consecutive failures

## License

MIT License
