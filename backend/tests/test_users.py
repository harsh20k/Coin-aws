import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_get_me_unauthorized():
    """Without auth header, protected route returns 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/users/me")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient, auth_headers: dict):
    r = await client.get("/users/me", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert "id" in data
    assert data["cognito_sub"].startswith("pytest-")
    assert data["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_put_me_upsert(client: AsyncClient, auth_headers: dict):
    r = await client.put("/users/me", json={"email": "updated@example.com"}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["email"] == "updated@example.com"
    r2 = await client.get("/users/me", headers=auth_headers)
    assert r2.json()["email"] == "updated@example.com"
