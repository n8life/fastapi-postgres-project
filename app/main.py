from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .database import db_manager, get_user_by_id


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


app = FastAPI(
    title="FastAPI PostgreSQL Demo",
    description="A simple FastAPI application that reads from a PostgreSQL database",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "FastAPI PostgreSQL Demo API"}


@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    """Get a user by ID from the database"""
    user = await get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}