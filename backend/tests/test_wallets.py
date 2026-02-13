import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_wallets_list_empty(client: AsyncClient, auth_headers: dict):
    r = await client.get("/wallets", headers=auth_headers)
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.asyncio
async def test_wallets_crud(client: AsyncClient, auth_headers: dict):
    # create
    r = await client.post("/wallets", json={"name": "Main"}, headers=auth_headers)
    assert r.status_code == 201
    data = r.json()
    wallet_id = data["id"]
    assert data["name"] == "Main"
    assert "user_id" in data

    # list
    r = await client.get("/wallets", headers=auth_headers)
    assert r.status_code == 200
    assert len(r.json()) >= 1
    assert any(w["id"] == wallet_id for w in r.json())

    # get one
    r = await client.get(f"/wallets/{wallet_id}", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["name"] == "Main"

    # update
    r = await client.put(f"/wallets/{wallet_id}", json={"name": "Updated"}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["name"] == "Updated"

    # delete
    r = await client.delete(f"/wallets/{wallet_id}", headers=auth_headers)
    assert r.status_code == 204
    r = await client.get(f"/wallets/{wallet_id}", headers=auth_headers)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_wallets_get_404(client: AsyncClient, auth_headers: dict):
    r = await client.get(
        "/wallets/00000000-0000-0000-0000-000000000000",
        headers=auth_headers,
    )
    assert r.status_code == 404
