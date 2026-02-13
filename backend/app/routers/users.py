from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user_id, get_token_payload
from app.database import get_db
from app.models import User
from app.schemas import UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_me(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.put("/me", response_model=UserResponse)
async def upsert_me(
    body: UserUpdate,
    payload: dict = Depends(get_token_payload),
    db: AsyncSession = Depends(get_db),
):
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing sub in token")
    result = await db.execute(select(User).where(User.cognito_sub == sub))
    user = result.scalar_one_or_none()
    if user:
        if body.email is not None:
            user.email = body.email
        await db.flush()
        await db.refresh(user)
        return user
    email = body.email if body.email is not None else payload.get("email")
    user = User(cognito_sub=sub, email=email)
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user
