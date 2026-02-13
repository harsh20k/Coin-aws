import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_subcategories_list(client: AsyncClient, auth_headers: dict):
    r = await client.get("/subcategories", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    # Default seed may have added system subcategories
    types = {s["transaction_type"] for s in data}
    assert "income" in types or "expense" in types or len(data) == 0


@pytest.mark.asyncio
async def test_subcategories_list_filter_by_type(client: AsyncClient, auth_headers: dict):
    r = await client.get("/subcategories?type=expense", headers=auth_headers)
    assert r.status_code == 200
    for s in r.json():
        assert s["transaction_type"] == "expense"


@pytest.mark.asyncio
async def test_subcategories_create_and_delete(client: AsyncClient, auth_headers: dict):
    r = await client.post(
        "/subcategories",
        json={"transaction_type": "expense", "name": "Test-Custom"},
        headers=auth_headers,
    )
    assert r.status_code == 201
    data = r.json()
    sub_id = data["id"]
    assert data["name"] == "Test-Custom"
    assert data["transaction_type"] == "expense"
    assert data["is_system"] is False

    r = await client.put(f"/subcategories/{sub_id}", json={"name": "Test-Updated"}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["name"] == "Test-Updated"

    r = await client.delete(f"/subcategories/{sub_id}", headers=auth_headers)
    assert r.status_code == 204
    r = await client.get("/subcategories?type=expense", headers=auth_headers)
    assert not any(s["id"] == sub_id for s in r.json())


@pytest.mark.asyncio
async def test_subcategories_delete_owned_only(client: AsyncClient, auth_headers: dict):
    """Deleting a non-existent or other user's subcategory returns 404."""
    r = await client.delete(
        "/subcategories/00000000-0000-0000-0000-000000000000",
        headers=auth_headers,
    )
    assert r.status_code == 404
