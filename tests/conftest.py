"""Pytest configuration and shared fixtures."""

import asyncio
from collections.abc import AsyncGenerator, Generator
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from alphasnob.domain.decisions.services.decision_engine import DecisionEngine
from alphasnob.domain.messaging.entities.chat import Chat, ChatType
from alphasnob.domain.messaging.entities.message import Message
from alphasnob.domain.messaging.value_objects.chat_id import ChatId
from alphasnob.domain.messaging.value_objects.message_content import MessageContent
from alphasnob.domain.users.entities.user import User
from alphasnob.domain.users.entities.user_profile import UserProfile
from alphasnob.domain.users.value_objects.relationship import Relationship, RelationshipLevel
from alphasnob.domain.users.value_objects.trust_score import TrustScore
from alphasnob.domain.users.value_objects.user_id import UserId
from alphasnob.infrastructure.config.settings import Settings
from alphasnob.infrastructure.persistence.database import Database


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings() -> Settings:
    """Create test settings."""
    return Settings(
        telegram={"api_id": 12345, "api_hash": "test_hash", "session_name": "test_session"},
        llm={
            "anthropic_api_key": "test_anthropic_key",
            "openai_api_key": "test_openai_key",
        },
        bot={
            "owner_id": 123456789,
            "owner_username": "test_owner",
            "response_probability": 0.3,
            "min_trust_for_response": 0.0,
            "max_cooldown_minutes": 60,
        },
        paths={
            "database": ":memory:",
            "logs_dir": "tests/logs",
            "data_dir": "tests/data",
        },
        debug=True,
    )


@pytest.fixture
async def test_database() -> AsyncGenerator[Database, None]:
    """Create in-memory test database."""
    db = Database("sqlite+aiosqlite:///:memory:", echo=False)
    await db.connect()
    await db.create_tables()
    yield db
    await db.disconnect()


@pytest.fixture
async def test_session(test_database: Database) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async with test_database.session() as session:
        yield session
        await session.rollback()


# Domain fixtures
@pytest.fixture
def user_id() -> UserId:
    """Create test user ID."""
    return UserId(123456789)


@pytest.fixture
def owner_user_id() -> UserId:
    """Create owner user ID."""
    return UserId(987654321)


@pytest.fixture
def test_user(user_id: UserId) -> User:
    """Create test user."""
    return User(
        user_id=user_id,
        username="test_user",
        first_name="Test",
        last_name="User",
    )


@pytest.fixture
def test_user_profile(user_id: UserId) -> UserProfile:
    """Create test user profile."""
    return UserProfile(
        user_id=user_id,
        username="test_user",
        first_name="Test",
        last_name="User",
        relationship=Relationship(level=RelationshipLevel.STRANGER),
        trust_score=TrustScore(0.5),
        interaction_count=0,
        positive_interactions=0,
        negative_interactions=0,
        last_interaction=None,
    )


@pytest.fixture
def owner_user_profile(owner_user_id: UserId) -> UserProfile:
    """Create owner user profile."""
    profile = UserProfile(
        user_id=owner_user_id,
        username="owner",
        first_name="Owner",
        last_name="User",
        relationship=Relationship(level=RelationshipLevel.OWNER),
        trust_score=TrustScore(1.0),
        interaction_count=1000,
        positive_interactions=1000,
        negative_interactions=0,
        last_interaction=datetime.now(UTC),
    )
    for topic in ["coding", "ai", "music"]:
        profile.add_detected_topic(topic)
    return profile


@pytest.fixture
def test_chat() -> Chat:
    """Create test chat."""
    return Chat(
        chat_id=ChatId(value=-123456789, chat_type=ChatType.PRIVATE),
        title=None,
        username="test_user",
        message_count=0,
        last_message_at=None,
    )


@pytest.fixture
def test_message(user_id: UserId) -> Message:
    """Create test message."""
    return Message(
        message_id=1,
        chat_id=ChatId(value=-123456789, chat_type=ChatType.PRIVATE),
        user_id=user_id,
        content=MessageContent("Hello, bot!"),
        timestamp=datetime.now(UTC),
        reply_to_message_id=None,
    )


@pytest.fixture
def decision_engine() -> DecisionEngine:
    """Create decision engine for testing."""
    return DecisionEngine(base_probability=0.3)


@pytest.fixture
def mock_uuid() -> UUID:
    """Create mock UUID for testing."""
    return uuid4()
