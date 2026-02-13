import enum
import uuid
from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import Boolean, BigInteger, Date, Enum, ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TransactionTypeEnum(str, enum.Enum):
    income = "income"
    expense = "expense"
    investment = "investment"
    donation = "donation"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cognito_sub: Mapped[str] = mapped_column(nullable=False, unique=True, index=True)
    email: Mapped[Optional[str]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)

    wallets: Mapped[List["Wallet"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    budgets: Mapped[List["Budget"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    goals: Mapped[List["Goal"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    subcategories: Mapped[List["Subcategory"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Wallet(Base):
    __tablename__ = "wallets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="wallets")
    transactions: Mapped[List["Transaction"]] = relationship(back_populates="wallet", cascade="all, delete-orphan")


class Subcategory(Base):
    __tablename__ = "subcategories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_type: Mapped[TransactionTypeEnum] = mapped_column(Enum(TransactionTypeEnum), nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)
    is_system: Mapped[bool] = mapped_column(nullable=False, default=False)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)

    __table_args__ = (UniqueConstraint("transaction_type", "name", "user_id", name="uq_subcategories_type_name_user"),)

    user: Mapped[Optional["User"]] = relationship(back_populates="subcategories")


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    wallet_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("wallets.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[TransactionTypeEnum] = mapped_column(Enum(TransactionTypeEnum), nullable=False)
    subcategory_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("subcategories.id"), nullable=False)
    amount_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)

    wallet: Mapped["Wallet"] = relationship(back_populates="transactions")


class Budget(Base):
    __tablename__ = "budgets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    subcategory_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("subcategories.id"), nullable=False)
    limit_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="budgets")


class Goal(Base):
    __tablename__ = "goals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(nullable=False)
    target_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    goal_type: Mapped[TransactionTypeEnum] = mapped_column(Enum(TransactionTypeEnum), nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="goals")
