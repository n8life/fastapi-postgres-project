import os
import pytest

# Ensure pytest-asyncio plugin is loaded
pytest_plugins = ("pytest_asyncio",)

@pytest.fixture(scope="session", autouse=True)
def _set_test_env():
    # Disable API key enforcement and HTTPS redirects in tests
    os.environ.setdefault("REQUIRE_API_KEY", "false")
    os.environ.setdefault("ENFORCE_HTTPS", "false")
    # Provide a benign default API_KEY to avoid None comparisons
    os.environ.setdefault("API_KEY", "test-api-key-123")
    # Flag to signal the app we're under pytest
    os.environ.setdefault("PYTEST_RUNNING", "1")

    # Apply FastAPI dependency override so routes skip auth in tests
    try:
        from app.main import app
        from app.security import get_api_key as _get_api_key
        app.dependency_overrides[_get_api_key] = lambda: ""
    except Exception:
        # If import ordering prevents this, tests will still pass due to env flags
        pass

    yield
