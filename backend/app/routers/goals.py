from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user_id
from app.database import get_db
from app.models import Goal, TransactionTypeEnum
from app.schemas import GoalCreate, GoalResponse, GoalUpdate, TransactionType

router = APIRouter(prefix="/goals", tags=["goals"])


def _schema_type(t: TransactionType) -> TransactionTypeEnum:
    return TransactionTypeEnum(t.value)


async def _get_goal_or_404(db: AsyncSession, id: UUID, user_id: UUID) -> Goal:
    result = await db.execute(select(Goal).where(Goal.id == id, Goal.user_id == user_id))
    g = result.scalar_one_or_none()
    if not g:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    return g


def _validate_period(period_start: date, period_end: date) -> None:
    if period_end < period_start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="period_end must be >= period_start",
        )


@router.get("", response_model=list[GoalResponse])
async def list_goals(
    period_start: date | None = Query(None),
    period_end: date | None = Query(None),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    q = select(Goal).where(Goal.user_id == user_id)
    if period_start is not None:
        q = q.where(Goal.period_end >= period_start)
    if period_end is not None:
        q = q.where(Goal.period_start <= period_end)
    result = await db.execute(q)
    return list(result.scalars().all())


@router.post("", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
async def create_goal(
    body: GoalCreate,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    _validate_period(body.period_start, body.period_end)
    g = Goal(
        user_id=user_id,
        title=body.title,
        target_cents=body.target_cents,
        goal_type=_schema_type(body.goal_type),
        period_start=body.period_start,
        period_end=body.period_end,
    )
    db.add(g)
    await db.flush()
    await db.refresh(g)
    return g


@router.get("/{id}", response_model=GoalResponse)
async def get_goal(
    id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await _get_goal_or_404(db, id, user_id)


@router.put("/{id}", response_model=GoalResponse)
async def update_goal(
    id: UUID,
    body: GoalUpdate,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    g = await _get_goal_or_404(db, id, user_id)
    if body.title is not None:
        g.title = body.title
    if body.target_cents is not None:
        g.target_cents = body.target_cents
    if body.goal_type is not None:
        g.goal_type = _schema_type(body.goal_type)
    if body.period_start is not None and body.period_end is not None:
        _validate_period(body.period_start, body.period_end)
        g.period_start = body.period_start
        g.period_end = body.period_end
    elif body.period_start is not None:
        _validate_period(body.period_start, g.period_end)
        g.period_start = body.period_start
    elif body.period_end is not None:
        _validate_period(g.period_start, body.period_end)
        g.period_end = body.period_end
    await db.flush()
    await db.refresh(g)
    return g


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_goal(
    id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    g = await _get_goal_or_404(db, id, user_id)
    await db.delete(g)
    return None
