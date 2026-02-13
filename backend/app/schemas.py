from datetime import date, datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TransactionType(str, Enum):
    income = "income"
    expense = "expense"
    investment = "investment"
    donation = "donation"


# ----- User -----
class UserBase(BaseModel):
    email: Optional[str] = None


class UserCreate(UserBase):
    cognito_sub: str


class UserUpdate(BaseModel):
    email: Optional[str] = None


class UserResponse(BaseModel):
    id: UUID
    cognito_sub: str
    email: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ----- Wallet -----
class WalletCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class WalletUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class WalletResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ----- Subcategory -----
class SubcategoryCreate(BaseModel):
    transaction_type: TransactionType
    name: str = Field(..., min_length=1, max_length=255)


class SubcategoryUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class SubcategoryResponse(BaseModel):
    id: UUID
    transaction_type: TransactionType
    name: str
    is_system: bool
    user_id: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)


# ----- Transaction -----
class TransactionCreate(BaseModel):
    wallet_id: UUID
    type: TransactionType
    subcategory_id: UUID
    amount_cents: int
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    transaction_date: date


class TransactionUpdate(BaseModel):
    type: Optional[TransactionType] = None
    subcategory_id: Optional[UUID] = None
    amount_cents: Optional[int] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    transaction_date: Optional[date] = None


class TransactionResponse(BaseModel):
    id: UUID
    wallet_id: UUID
    type: TransactionType
    subcategory_id: UUID
    amount_cents: int
    description: Optional[str] = None
    tags: List[str]
    transaction_date: date
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ----- Budget -----
class BudgetCreate(BaseModel):
    subcategory_id: UUID
    limit_cents: int
    period_start: date
    period_end: date


class BudgetUpdate(BaseModel):
    subcategory_id: Optional[UUID] = None
    limit_cents: Optional[int] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None


class BudgetResponse(BaseModel):
    id: UUID
    user_id: UUID
    subcategory_id: UUID
    limit_cents: int
    period_start: date
    period_end: date
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ----- Goal -----
class GoalCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    target_cents: int
    goal_type: TransactionType
    period_start: date
    period_end: date


class GoalUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    target_cents: Optional[int] = None
    goal_type: Optional[TransactionType] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None


class GoalResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    target_cents: int
    goal_type: TransactionType
    period_start: date
    period_end: date
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ----- Chat -----
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    reply: str
