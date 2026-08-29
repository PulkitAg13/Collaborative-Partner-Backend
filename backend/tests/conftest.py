"""Shared test fixtures and helpers."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.agents.collaborative_agent import AgentService, create_agent_service
from app.db.database import Base, get_db
from app.main import app

# ---------------------------------------------------------------------------
# In-memory SQLite for tests — fully isolated from app.db
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = "sqlite://"  # in-memory

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = sessionmaker(
    bind=test_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


@pytest.fixture(autouse=True)
def setup_test_db():
    """Create all tables before each test and drop them after."""
    from app.db import models  # noqa: F401 — register models

    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    """Provide a test database session."""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Mock agent — deterministic, no Gemini key needed
# ---------------------------------------------------------------------------
class _FixedMockAgent(AgentService):
    """Always returns the same response for predictable assertions."""

    async def generate_response(self, conversation_history, user_message, preferences):
        pref_note = ""
        if preferences:
            pref_note = " (adapted to preferences)"
        return f"Mock response to: {user_message}{pref_note}", "clarifying_question"


@pytest.fixture
def mock_agent() -> AgentService:
    return _FixedMockAgent()


# ---------------------------------------------------------------------------
# TestClient with overridden dependencies
# ---------------------------------------------------------------------------
@pytest.fixture
def client(mock_agent):
    """FastAPI test client with in-memory DB and mock agent."""

    def override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    def override_get_agent():
        return mock_agent

    from app.api.routes.chat import get_agent_service
    from app.agents.collaborative_agent import create_agent_service

    # Clear cached singleton so each test gets the mock
    create_agent_service.cache_clear()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_agent_service] = override_get_agent

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
    create_agent_service.cache_clear()
