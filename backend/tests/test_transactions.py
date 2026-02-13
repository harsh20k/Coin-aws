from datetime import date
from uuid import uuid4

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_transactions_require_wallet(client: AsyncClient, auth_headers: dict):
    """Create wallet and subcategory first, then transaction."""
    rw = await client.post("/wallets", json={"name": "Tx-Wallet"}, headers=auth_headers)
    assert rw.status_code == 201
    wallet_id = rw.json()["id"]

    rsc = await client.get("/subcategories?type=expense", headers=auth_headers)
    assert rsc.status_code == 200
    subs = rsc.json()
    assert len(subs) >= 1
    subcategory_id = subs[0]["id"]

    r = await client.post(
        "/transactions",
        json={
            "wallet_id": wallet_id,
            "type": "expense",
            "subcategory_id": subcategory_id,
            "amount_cents": 1000,
            "description": "Test",
            "tags": ["food"],
            "transaction_date": date.today().isoformat(),
        },
        headers=auth_headers,
    )
    assert r.status_code == 201
    data = r.json()
    assert data["amount_cents"] == 1000
    assert data["type"] == "expense"
    tx_id = data["id"]

    r = await client.get("/transactions", headers=auth_headers)
    assert r.status_code == 200
    assert any(t["id"] == tx_id for t in r.json())

    r = await client.get(f"/transactions/{tx_id}", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["description"] == "Test"

    r = await client.put(
        f"/transactions/{tx_id}",
        json={"amount_cents": 2000},
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert r.json()["amount_cents"] == 2000

    r = await client.delete(f"/transactions/{tx_id}", headers=auth_headers)
    assert r.status_code == 204
    r = await client.get(f"/transactions/{tx_id}", headers=auth_headers)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_transactions_list_filters(client: AsyncClient, auth_headers: dict):
    r = await client.get(
        "/transactions",
        params={"type": "income", "date_from": "2020-01-01", "date_to": "2030-12-31"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_transactions_wallet_other_user_404(client: AsyncClient, auth_headers: dict):
    """Create with non-owned wallet_id returns 404."""
    fake_wallet_id = str(uuid4())
    rsc = await client.get("/subcategories?type=expense", headers=auth_headers)
    subcategory_id = rsc.json()[0]["id"]
    r = await client.post(
        "/transactions",
        json={
            "wallet_id": fake_wallet_id,
            "type": "expense",
            "subcategory_id": subcategory_id,
            "amount_cents": 100,
            "transaction_date": date.today().isoformat(),
        },
        headers=auth_headers,
    )
    assert r.status_code == 404
