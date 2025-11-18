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
- CLI command execution with security validation

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

**Pull Messages for an Agent:**
```bash
# Get all messages for an agent (sent and received)
curl -X GET http://localhost:8000/agents/{agent_id}/messages

# Get only unread messages for an agent
curl -X GET http://localhost:8000/agents/{agent_id}/messages/unread

# Get message metadata with agent access control
curl -X GET http://localhost:8000/messages/{message_id}/metadata/{agent_id}

# Mark messages as read up to a specific date
curl -X PUT http://localhost:8000/agents/{agent_id}/messages/mark-read \
  -H "Content-Type: application/json" \
  -d '{"read_up_to_date": "2024-01-01T12:00:00Z"}'
```

**Create a Conversation:**
```bash
curl -X POST http://localhost:8000/conversations \
  -H "Content-Type: application/json" \
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
curl -X GET http://localhost:8000/conversations/{conversation_id}/details

# Get just conversation metadata
curl -X GET http://localhost:8000/conversations/{conversation_id}

# List all conversations
curl -X GET http://localhost:8000/conversations
```

**Execute CLI Commands:**
```bash
# Echo a message to the command line
curl -X POST http://localhost:8000/cli/echo \
  -H "Content-Type: application/json" \
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

## Environment Variables

- `DATABASE_URL`: PostgreSQL connection string (uses asyncpg driver)
  - Default: `postgresql+asyncpg://postgres:password@localhost:5432/testdb`

## Security Features

- Environment-based database credentials
- Connection pooling to prevent connection exhaustion
- Input validation with Pydantic models
- Proper error handling and HTTP status codes
- **Agent isolation**: Agents can only access their own messages (sender/recipient)
- **Access control**: Message metadata endpoints verify agent access permissions
- **Data privacy**: No endpoint allows accessing multiple agents' information simultaneously
- **CLI security**: Command injection prevention through strict input validation and safe shell escaping
- **Command restrictions**: Only safe alphanumeric characters and basic punctuation allowed in CLI commands

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

The application supports multiple deployment methods:

### Docker Compose (Recommended for Development)

```bash
# Build and run with Docker Compose
docker-compose up --build -d

# Check container health status
docker-compose ps

# Scale the application
docker-compose up --scale app=3
```

### Kubernetes Deployment (Production Ready)

The application includes comprehensive Kubernetes manifests for production deployment:

#### Prerequisites
- Kubernetes cluster (local or cloud)
- `kubectl` configured to access your cluster
- Docker for building images

#### Quick Deployment

```bash
# Deploy using the provided script
cd k8s
./deploy.sh
```

#### Manual Deployment

```bash
# Build the Docker image
docker build -t fastapi-postgres-app:latest .

# Apply Kubernetes manifests in order
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/postgres-storage.yaml
kubectl apply -f k8s/postgres-deployment.yaml
kubectl apply -f k8s/fastapi-deployment.yaml
kubectl apply -f k8s/services.yaml
```

#### Accessing the Application

**Option 1: LoadBalancer (if supported):**
```bash
# Get external IP
kubectl get svc fastapi-service -n fastapi-postgres
# Access via external IP on port 80
```

**Option 2: Port Forward (for local/development clusters):**
```bash
# Forward port to localhost
kubectl port-forward svc/fastapi-service 8000:80 -n fastapi-postgres
# Access at http://localhost:8000
```

**Option 3: NodePort (alternative):**
```bash
# Change service type to NodePort in services.yaml
# Then access via node IP and assigned port
kubectl get nodes -o wide
kubectl get svc fastapi-service -n fastapi-postgres
```

#### Kubernetes Resources

The deployment creates the following resources:

- **Namespace**: `fastapi-postgres` - Isolated environment for all resources
- **Persistent Volume**: Local storage for PostgreSQL data (1Gi)
- **PostgreSQL**: Single replica with health checks and resource limits
- **FastAPI**: 2 replicas with health checks and horizontal scaling capability
- **Services**: ClusterIP for PostgreSQL, LoadBalancer for FastAPI

#### Monitoring Deployment

```bash
# Check deployment status
kubectl get pods -n fastapi-postgres
kubectl get services -n fastapi-postgres

# View logs
kubectl logs -f deployment/fastapi-app -n fastapi-postgres
kubectl logs -f deployment/postgres -n fastapi-postgres

# Check resource usage
kubectl top pods -n fastapi-postgres
```

#### Scaling

```bash
# Scale FastAPI application
kubectl scale deployment fastapi-app --replicas=5 -n fastapi-postgres

# Check scaling status
kubectl get deployments -n fastapi-postgres
```

#### Cleanup

```bash
# Use cleanup script
cd k8s
./cleanup.sh

# Or manually delete resources
kubectl delete namespace fastapi-postgres
```

#### Production Considerations

1. **Storage**: Replace local volumes with cloud-based persistent volumes
2. **Security**: Use secrets for database credentials instead of plain text
3. **Networking**: Configure ingress controllers for proper domain routing
4. **Monitoring**: Add Prometheus/Grafana monitoring
5. **Backup**: Implement PostgreSQL backup strategies
6. **SSL/TLS**: Configure certificates for HTTPS

#### Available Scripts

- `k8s/deploy.sh`: Automated deployment script
- `k8s/cleanup.sh`: Complete cleanup script

### Health Monitoring

The Docker container includes a built-in healthcheck that:
- Tests the `/health` endpoint every 30 seconds
- Allows 10 seconds timeout per check
- Waits 5 seconds before starting checks
- Marks container unhealthy after 3 consecutive failures

## License

MIT License
