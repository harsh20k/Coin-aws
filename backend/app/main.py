from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.database import async_session_factory
from app.models import Subcategory, TransactionTypeEnum
from app.routers import budgets, chat, goals, subcategories, transactions, users, wallets


DEFAULT_SUBCATEGORIES = [
    (TransactionTypeEnum.income, "Salary"),
    (TransactionTypeEnum.income, "Freelance"),
    (TransactionTypeEnum.income, "Other"),
    (TransactionTypeEnum.expense, "Food"),
    (TransactionTypeEnum.expense, "Transport"),
    (TransactionTypeEnum.expense, "Utilities"),
    (TransactionTypeEnum.expense, "Shopping"),
    (TransactionTypeEnum.expense, "Other"),
    (TransactionTypeEnum.investment, "Stocks"),
    (TransactionTypeEnum.investment, "Savings"),
    (TransactionTypeEnum.investment, "Other"),
    (TransactionTypeEnum.donation, "Charity"),
    (TransactionTypeEnum.donation, "Other"),
]


async def seed_default_subcategories():
    async with async_session_factory() as session:
        for tx_type, name in DEFAULT_SUBCATEGORIES:
            r = await session.execute(
                select(Subcategory).where(
                    Subcategory.transaction_type == tx_type,
                    Subcategory.name == name,
                    Subcategory.user_id.is_(None),
                )
            )
            if r.scalar_one_or_none() is None:
                session.add(
                    Subcategory(transaction_type=tx_type, name=name, is_system=True, user_id=None)
                )
        await session.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await seed_default_subcategories()
    yield


app = FastAPI(title="Dalla API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(wallets.router)
app.include_router(subcategories.router)
app.include_router(transactions.router)
app.include_router(budgets.router)
app.include_router(goals.router)
app.include_router(chat.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
