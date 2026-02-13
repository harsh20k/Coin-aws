from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user_id
from app.database import get_db
from app.models import Wallet
from app.schemas import WalletCreate, WalletResponse, WalletUpdate

router = APIRouter(prefix="/wallets", tags=["wallets"])


async def _get_wallet_or_404(db: AsyncSession, wallet_id: UUID, user_id: UUID) -> Wallet:
    result = await db.execute(select(Wallet).where(Wallet.id == wallet_id, Wallet.user_id == user_id))
    wallet = result.scalar_one_or_none()
    if not wallet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")
    return wallet


@router.get("", response_model=list[WalletResponse])
async def list_wallets(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Wallet).where(Wallet.user_id == user_id))
    return list(result.scalars().all())


@router.post("", response_model=WalletResponse, status_code=status.HTTP_201_CREATED)
async def create_wallet(
    body: WalletCreate,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    wallet = Wallet(user_id=user_id, name=body.name)
    db.add(wallet)
    await db.flush()
    await db.refresh(wallet)
    return wallet


@router.get("/{id}", response_model=WalletResponse)
async def get_wallet(
    id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await _get_wallet_or_404(db, id, user_id)


@router.put("/{id}", response_model=WalletResponse)
async def update_wallet(
    id: UUID,
    body: WalletUpdate,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    wallet = await _get_wallet_or_404(db, id, user_id)
    wallet.name = body.name
    await db.flush()
    await db.refresh(wallet)
    return wallet


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_wallet(
    id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    wallet = await _get_wallet_or_404(db, id, user_id)
    await db.delete(wallet)
    return None
