import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_chat_stub(client: AsyncClient, auth_headers: dict):
    r = await client.post("/chat", json={"message": "What was my biggest expense?"}, headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert "reply" in data
    assert isinstance(data["reply"], str)
    assert "stub" in data["reply"].lower() or "Bedrock" in data["reply"]
