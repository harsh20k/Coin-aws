from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user_id
from app.database import get_db
from app.models import Budget
from app.schemas import BudgetCreate, BudgetResponse, BudgetUpdate

router = APIRouter(prefix="/budgets", tags=["budgets"])


async def _get_budget_or_404(db: AsyncSession, id: UUID, user_id: UUID) -> Budget:
    result = await db.execute(select(Budget).where(Budget.id == id, Budget.user_id == user_id))
    b = result.scalar_one_or_none()
    if not b:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")
    return b


def _validate_period(period_start: date, period_end: date) -> None:
    if period_end < period_start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="period_end must be >= period_start",
        )


@router.get("", response_model=list[BudgetResponse])
async def list_budgets(
    period_start: date | None = Query(None),
    period_end: date | None = Query(None),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    q = select(Budget).where(Budget.user_id == user_id)
    if period_start is not None:
        q = q.where(Budget.period_end >= period_start)
    if period_end is not None:
        q = q.where(Budget.period_start <= period_end)
    result = await db.execute(q)
    return list(result.scalars().all())


@router.post("", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
async def create_budget(
    body: BudgetCreate,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    _validate_period(body.period_start, body.period_end)
    b = Budget(
        user_id=user_id,
        subcategory_id=body.subcategory_id,
        limit_cents=body.limit_cents,
        period_start=body.period_start,
        period_end=body.period_end,
    )
    db.add(b)
    await db.flush()
    await db.refresh(b)
    return b


@router.get("/{id}", response_model=BudgetResponse)
async def get_budget(
    id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await _get_budget_or_404(db, id, user_id)


@router.put("/{id}", response_model=BudgetResponse)
async def update_budget(
    id: UUID,
    body: BudgetUpdate,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    b = await _get_budget_or_404(db, id, user_id)
    if body.subcategory_id is not None:
        b.subcategory_id = body.subcategory_id
    if body.limit_cents is not None:
        b.limit_cents = body.limit_cents
    if body.period_start is not None and body.period_end is not None:
        _validate_period(body.period_start, body.period_end)
        b.period_start = body.period_start
        b.period_end = body.period_end
    elif body.period_start is not None:
        _validate_period(body.period_start, b.period_end)
        b.period_start = body.period_start
    elif body.period_end is not None:
        _validate_period(b.period_start, body.period_end)
        b.period_end = body.period_end
    await db.flush()
    await db.refresh(b)
    return b


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_budget(
    id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    b = await _get_budget_or_404(db, id, user_id)
    await db.delete(b)
    return None
