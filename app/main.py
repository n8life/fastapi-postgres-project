from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from .database import db_manager, get_user_by_id
from .routers.messaging import router as messaging_router
from .routers.cli import router as cli_router
from .routers.s3 import router as s3_router
from .security import (
    get_api_key, 
    HTTPSEnforcementMiddleware, 
    SecurityHeadersMiddleware,
    get_security_config
)


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    created_at: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    await db_manager.create_pool()
    yield
    # Shutdown
    await db_manager.close_pool()


# Get security configuration
security_config = get_security_config()

app = FastAPI(
    title="FastAPI PostgreSQL Demo",
    description="A comprehensive FastAPI application that provides messaging capabilities between agents, command-line interface operations, and user management with PostgreSQL backend.",
    version="1.0.0",
    lifespan=lifespan
)

# Add security middleware
if security_config["enforce_https"]:
    app.add_middleware(HTTPSEnforcementMiddleware, enforce_https=True)

app.add_middleware(SecurityHeadersMiddleware)

# Include routers
app.include_router(messaging_router)
app.include_router(cli_router)
app.include_router(s3_router)


@app.get("/")
async def root(api_key: str = Depends(get_api_key)):
    """Root endpoint"""
    return {"message": "FastAPI PostgreSQL Demo API"}


@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, api_key: str = Depends(get_api_key)):
    """Get a user by ID from the database"""
    user = await get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.get("/health")
async def health_check(api_key: str = Depends(get_api_key)):
    """Health check endpoint"""
    return {"status": "healthy"}
