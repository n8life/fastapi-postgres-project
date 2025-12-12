import os
import pytest

@pytest.fixture(scope="session", autouse=True)
def _set_test_env():
    # Disable API key enforcement and HTTPS redirects in tests
    os.environ.setdefault("REQUIRE_API_KEY", "false")
    os.environ.setdefault("ENFORCE_HTTPS", "false")
    # Provide a benign default API_KEY to avoid None comparisons
    os.environ.setdefault("API_KEY", "test-api-key-123")
    # Flag to signal the app we're under pytest
    os.environ.setdefault("PYTEST_RUNNING", "1")
    yield
