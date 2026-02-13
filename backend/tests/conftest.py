import uuid
from uuid import UUID

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.auth import get_current_user_id, get_token_payload
from app.config import settings
from app.database import get_db
from app.main import app
from app.models import User

pytest_plugins = ("pytest_asyncio",)

# Separate engine with NullPool so test fixtures don't share connections with the app.
_test_engine = create_async_engine(settings.database_url, poolclass=NullPool, echo=False)
test_session_factory = async_sessionmaker(
    _test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def test_user():
    """Create a test user in DB; yield (user_id, cognito_sub) for auth overrides."""
    async with test_session_factory() as session:
        sub = f"pytest-{uuid.uuid4()}"
        user = User(cognito_sub=sub, email="test@example.com")
        session.add(user)
        await session.commit()
        await session.refresh(user)
        user_id, cognito_sub = user.id, user.cognito_sub
    yield (user_id, cognito_sub)
    async with test_session_factory() as session:
        r = await session.execute(select(User).where(User.cognito_sub == cognito_sub))
        u = r.scalar_one_or_none()
        if u:
            await session.delete(u)
            await session.commit()


@pytest.fixture
async def client(test_user):
    """Async HTTP client with auth overrides so no real Cognito is needed."""
    user_id, cognito_sub = test_user

    async def override_get_current_user_id() -> UUID:
        return user_id

    def override_get_token_payload() -> dict:
        return {"sub": cognito_sub, "email": "test@example.com"}

    async def override_get_db():
        async with test_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app.dependency_overrides[get_current_user_id] = override_get_current_user_id
    app.dependency_overrides[get_token_payload] = override_get_token_payload
    app.dependency_overrides[get_db] = override_get_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
async def auth_headers():
    """Use with client; client already has overrides, so any Bearer token is accepted."""
    return {"Authorization": "Bearer pytest-token"}
