"""
Shared pytest fixtures for MediGenie.
"""

from __future__ import annotations

import pytest
import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

try:
    from fastapi.testclient import TestClient
except Exception:  # pragma: no cover - fallback for incompatible deps
    TestClient = None


def _create_test_client(app):
    """Create a test client compatible with the local httpx/starlette stack."""
    if TestClient is None:
        raise RuntimeError("FastAPI TestClient is unavailable")

    try:
        return TestClient(app)
    except TypeError:
        transport = httpx.ASGITransport(app=app)

        # httpx.ASGITransport in newer httpx exposes async handling only.
        # Provide a tiny synchronous wrapper implementing `handle_request`
        # so httpx.Client can call it in this test environment.
        if not hasattr(transport, "handle_request"):
            class _SyncTransportWrapper:
                def __init__(self, inner):
                    self._inner = inner

                def handle_request(self, request):
                    import asyncio

                    loop = asyncio.new_event_loop()
                    try:
                        async_resp = loop.run_until_complete(
                            self._inner.handle_async_request(request)
                        )

                        # Read full content from async response and construct
                        # a synchronous httpx.Response with a sync byte stream.
                        content = loop.run_until_complete(async_resp.aread())

                        import httpx as _httpx

                        # Remove encoding headers since we've already read raw bytes
                        headers = dict(async_resp.headers)
                        headers.pop("content-encoding", None)
                        headers.pop("transfer-encoding", None)

                        sync_resp = _httpx.Response(
                            status_code=async_resp.status_code,
                            headers=headers,
                            content=content,
                            request=request,
                        )

                        return sync_resp
                    finally:
                        loop.close()

            transport = _SyncTransportWrapper(transport)

        return httpx.Client(transport=transport, base_url="http://testserver")

from app.db.session import get_db
from app.main import app
from app.models.models import Base

TEST_DATABASE_URL = "sqlite:///./test_medigenie.db"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """
    Create all database tables before tests
    and drop them afterwards.
    """

    # Ensure a clean database state for the test session
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    yield

    Base.metadata.drop_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client():
    """
    Shared FastAPI test client.
    """
    try:
        return _create_test_client(app)
    except Exception as exc:
        pytest.skip(
            f"FastAPI TestClient instantiation failed in this environment: {exc}"
        )