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

- `GET /` - Root endpoint with welcome message
- `GET /health` - Health check endpoint
- `GET /users/{user_id}` - Get user by ID from database

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