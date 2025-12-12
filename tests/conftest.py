import os
import pytest

# Ensure pytest-asyncio plugin is loaded
pytest_plugins = ("pytest_asyncio",)

# Auto-mark any async test functions with @pytest.mark.asyncio
def pytest_collection_modifyitems(items):
    import inspect
    import pytest as _pytest
    for item in items:
        func = getattr(item, "function", None)
        obj = getattr(item, "obj", None)
        # unwrap patched functions
        wrapped = getattr(obj, "__wrapped__", None)
        target = wrapped or obj
        is_coro = (func and inspect.iscoroutinefunction(func)) or (target and inspect.iscoroutinefunction(target))
        if is_coro and not item.get_closest_marker("asyncio"):
            item.add_marker(_pytest.mark.asyncio)
        # Targeted fallback for stubborn patched test
        if "tests/test_s3.py::TestS3Endpoints::test_pull_file_endpoint_success" in item.nodeid and not item.get_closest_marker("asyncio"):
            item.add_marker(_pytest.mark.asyncio)

# Fallback: run coroutine tests manually if plugin didn't intercept
def pytest_pyfunc_call(pyfuncitem):
    import inspect, asyncio
    testfunc = pyfuncitem.obj
    if inspect.iscoroutinefunction(testfunc):
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            loop.run_until_complete(testfunc(**pyfuncitem.funcargs))
        finally:
            try:
                loop.run_until_complete(loop.shutdown_asyncgens())
            finally:
                asyncio.set_event_loop(None)
                loop.close()
        return True

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
