from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user_id
from app.database import get_db
from app.models import Subcategory, TransactionTypeEnum
from app.schemas import SubcategoryCreate, SubcategoryResponse, SubcategoryUpdate, TransactionType

router = APIRouter(prefix="/subcategories", tags=["subcategories"])


def _schema_type(t: TransactionType) -> TransactionTypeEnum:
    return TransactionTypeEnum(t.value)


async def _get_owned_subcategory_or_404(db: AsyncSession, id: UUID, user_id: UUID) -> Subcategory:
    result = await db.execute(select(Subcategory).where(Subcategory.id == id, Subcategory.user_id == user_id))
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subcategory not found")
    return sub


@router.get("", response_model=list[SubcategoryResponse])
async def list_subcategories(
    type: TransactionType | None = Query(None, description="Filter by transaction type"),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    q = select(Subcategory).where(or_(Subcategory.user_id.is_(None), Subcategory.user_id == user_id))
    if type is not None:
        q = q.where(Subcategory.transaction_type == _schema_type(type))
    result = await db.execute(q)
    return list(result.scalars().all())


@router.post("", response_model=SubcategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_subcategory(
    body: SubcategoryCreate,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    sub = Subcategory(
        transaction_type=_schema_type(body.transaction_type),
        name=body.name,
        is_system=False,
        user_id=user_id,
    )
    db.add(sub)
    await db.flush()
    await db.refresh(sub)
    return sub


@router.put("/{id}", response_model=SubcategoryResponse)
async def update_subcategory(
    id: UUID,
    body: SubcategoryUpdate,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    sub = await _get_owned_subcategory_or_404(db, id, user_id)
    sub.name = body.name
    await db.flush()
    await db.refresh(sub)
    return sub


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subcategory(
    id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    sub = await _get_owned_subcategory_or_404(db, id, user_id)
    await db.delete(sub)
    return None
