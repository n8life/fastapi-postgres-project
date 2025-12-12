import os
from typing import Optional
from fastapi import HTTPException, Request, status, Depends
from fastapi.security import APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


# API Key configuration
API_KEY_NAME = "X-API-Key"
API_KEY = os.getenv("API_KEY", "************")  # Default redacted for security

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


async def get_api_key(api_key: Optional[str] = Depends(api_key_header)) -> str:
    """
    Validates the API key from the X-API-Key header.
    
    If REQUIRE_API_KEY is set to "false", this function will allow requests without
    an API key (useful for local testing), preserving security in other environments.
    
    Args:
        api_key: The API key from the header
        
    Returns:
        str: The validated API key or an empty string when API key enforcement is disabled
        
    Raises:
        HTTPException: If API key is missing or invalid while enforcement is enabled
    """
    # Allow global bypass when running tests
    if os.getenv("PYTEST_RUNNING", "").lower() in {"1", "true", "yes"}:
        return api_key or ""

    require_api_key = os.getenv("REQUIRE_API_KEY", "true").lower() == "true"
    if not require_api_key:
        # Auth disabled (e.g., tests); return a benign value
        return api_key or ""

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key"
        )
    
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return api_key


class HTTPSEnforcementMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce HTTPS connections in production.
    """
    
    def __init__(self, app, enforce_https: bool = True):
        super().__init__(app)
        self.enforce_https = enforce_https
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Only enforce HTTPS in production/non-localhost environments
        if (self.enforce_https and 
            not request.url.scheme == "https" and 
            request.client.host not in ["127.0.0.1", "localhost"]):
            
            # Redirect to HTTPS
            https_url = request.url.replace(scheme="https")
            from starlette.responses import RedirectResponse
            return RedirectResponse(url=str(https_url), status_code=301)
        
        response = await call_next(request)
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.
    """
    
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response


def get_security_config() -> dict:
    """
    Get security configuration from environment variables.
    
    Returns:
        dict: Security configuration
    """
    return {
        "enforce_https": os.getenv("ENFORCE_HTTPS", "true").lower() == "true",
        "api_key": API_KEY,
        "require_api_key": os.getenv("REQUIRE_API_KEY", "true").lower() == "true"
    }