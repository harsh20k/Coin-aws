from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user_id
from app.database import get_db
from app.models import Transaction, TransactionTypeEnum, Wallet
from app.schemas import TransactionCreate, TransactionResponse, TransactionType, TransactionUpdate

router = APIRouter(prefix="/transactions", tags=["transactions"])


def _schema_type(t: TransactionType) -> TransactionTypeEnum:
    return TransactionTypeEnum(t.value)


async def _get_wallet_owned_or_404(db: AsyncSession, wallet_id: UUID, user_id: UUID) -> Wallet:
    result = await db.execute(select(Wallet).where(Wallet.id == wallet_id, Wallet.user_id == user_id))
    w = result.scalar_one_or_none()
    if not w:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")
    return w


async def _get_transaction_owned_or_404(db: AsyncSession, id: UUID, user_id: UUID) -> Transaction:
    result = await db.execute(
        select(Transaction).join(Wallet).where(Transaction.id == id, Wallet.user_id == user_id)
    )
    tx = result.scalar_one_or_none()
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return tx


@router.get("", response_model=list[TransactionResponse])
async def list_transactions(
    wallet_id: UUID | None = Query(None),
    type: TransactionType | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    q = select(Transaction).join(Wallet).where(Wallet.user_id == user_id)
    if wallet_id is not None:
        q = q.where(Transaction.wallet_id == wallet_id)
    if type is not None:
        q = q.where(Transaction.type == _schema_type(type))
    if date_from is not None:
        q = q.where(Transaction.transaction_date >= date_from)
    if date_to is not None:
        q = q.where(Transaction.transaction_date <= date_to)
    q = q.order_by(Transaction.transaction_date.desc(), Transaction.created_at.desc())
    result = await db.execute(q)
    return list(result.scalars().all())


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    body: TransactionCreate,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await _get_wallet_owned_or_404(db, body.wallet_id, user_id)
    tx = Transaction(
        wallet_id=body.wallet_id,
        type=_schema_type(body.type),
        subcategory_id=body.subcategory_id,
        amount_cents=body.amount_cents,
        description=body.description,
        tags=body.tags or [],
        transaction_date=body.transaction_date,
    )
    db.add(tx)
    await db.flush()
    await db.refresh(tx)
    return tx


@router.get("/{id}", response_model=TransactionResponse)
async def get_transaction(
    id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await _get_transaction_owned_or_404(db, id, user_id)


@router.put("/{id}", response_model=TransactionResponse)
async def update_transaction(
    id: UUID,
    body: TransactionUpdate,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    tx = await _get_transaction_owned_or_404(db, id, user_id)
    if body.type is not None:
        tx.type = _schema_type(body.type)
    if body.subcategory_id is not None:
        tx.subcategory_id = body.subcategory_id
    if body.amount_cents is not None:
        tx.amount_cents = body.amount_cents
    if body.description is not None:
        tx.description = body.description
    if body.tags is not None:
        tx.tags = body.tags
    if body.transaction_date is not None:
        tx.transaction_date = body.transaction_date
    await db.flush()
    await db.refresh(tx)
    return tx


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    tx = await _get_transaction_owned_or_404(db, id, user_id)
    await db.delete(tx)
    return None
