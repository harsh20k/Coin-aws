from datetime import date

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_budgets_crud(client: AsyncClient, auth_headers: dict):
    rsc = await client.get("/subcategories?type=expense", headers=auth_headers)
    assert rsc.status_code == 200
    subcategory_id = rsc.json()[0]["id"]

    start = date(2025, 1, 1)
    end = date(2025, 1, 31)
    r = await client.post(
        "/budgets",
        json={
            "subcategory_id": subcategory_id,
            "limit_cents": 50000,
            "period_start": start.isoformat(),
            "period_end": end.isoformat(),
        },
        headers=auth_headers,
    )
    assert r.status_code == 201
    data = r.json()
    budget_id = data["id"]
    assert data["limit_cents"] == 50000

    r = await client.get("/budgets", headers=auth_headers)
    assert r.status_code == 200
    assert any(b["id"] == budget_id for b in r.json())

    r = await client.put(
        f"/budgets/{budget_id}",
        json={"limit_cents": 60000},
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert r.json()["limit_cents"] == 60000

    r = await client.delete(f"/budgets/{budget_id}", headers=auth_headers)
    assert r.status_code == 204


@pytest.mark.asyncio
async def test_budgets_invalid_period(client: AsyncClient, auth_headers: dict):
    rsc = await client.get("/subcategories?type=expense", headers=auth_headers)
    subcategory_id = rsc.json()[0]["id"]
    r = await client.post(
        "/budgets",
        json={
            "subcategory_id": subcategory_id,
            "limit_cents": 1000,
            "period_start": "2025-01-31",
            "period_end": "2025-01-01",
        },
        headers=auth_headers,
    )
    assert r.status_code == 400
