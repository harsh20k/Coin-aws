from datetime import date

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_goals_crud(client: AsyncClient, auth_headers: dict):
    start = date(2025, 2, 1)
    end = date(2025, 2, 28)
    r = await client.post(
        "/goals",
        json={
            "title": "Invest $500",
            "target_cents": 50000,
            "goal_type": "investment",
            "period_start": start.isoformat(),
            "period_end": end.isoformat(),
        },
        headers=auth_headers,
    )
    assert r.status_code == 201
    data = r.json()
    goal_id = data["id"]
    assert data["title"] == "Invest $500"
    assert data["goal_type"] == "investment"
    assert data["target_cents"] == 50000

    r = await client.get("/goals", headers=auth_headers)
    assert r.status_code == 200
    assert any(g["id"] == goal_id for g in r.json())

    r = await client.get(f"/goals/{goal_id}", headers=auth_headers)
    assert r.status_code == 200

    r = await client.put(
        f"/goals/{goal_id}",
        json={"title": "Invest $600", "target_cents": 60000},
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert r.json()["title"] == "Invest $600"
    assert r.json()["target_cents"] == 60000

    r = await client.delete(f"/goals/{goal_id}", headers=auth_headers)
    assert r.status_code == 204
    r = await client.get(f"/goals/{goal_id}", headers=auth_headers)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_goals_invalid_period(client: AsyncClient, auth_headers: dict):
    r = await client.post(
        "/goals",
        json={
            "title": "Bad period",
            "target_cents": 100,
            "goal_type": "income",
            "period_start": "2025-12-31",
            "period_end": "2025-01-01",
        },
        headers=auth_headers,
    )
    assert r.status_code == 400
