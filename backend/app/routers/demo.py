"""Demo data loader for testing the AI chat feature."""
import enum
from datetime import date, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user_id
from app.database import get_db
from app.models import Budget, Goal, Subcategory, Transaction, TransactionTypeEnum, Wallet
from app.schemas import DemoLoadRequest, DemoLoadResponse

router = APIRouter(prefix="/demo", tags=["demo"])

_TODAY = date(2026, 2, 23)


def _d(days_ago: int) -> date:
    return _TODAY - timedelta(days=days_ago)


# ---------------------------------------------------------------------------
# Profile data definitions
# ---------------------------------------------------------------------------

# Each entry: (type, subcategory_name, amount_cents, description, days_ago)
_FREQUENT_SHOPPER_TRANSACTIONS = [
    # -- Income --
    ("income", "Salary", 450000, "Monthly salary", 85),
    ("income", "Salary", 450000, "Monthly salary", 55),
    ("income", "Salary", 450000, "Monthly salary", 25),
    ("income", "Freelance", 80000, "Design project", 70),
    ("income", "Freelance", 55000, "Consulting gig", 40),
    # -- Food --
    ("expense", "Food", 6800, "Groceries – Whole Foods", 84),
    ("expense", "Food", 4200, "DoorDash delivery", 80),
    ("expense", "Food", 7100, "Groceries – Trader Joe's", 75),
    ("expense", "Food", 5500, "Restaurant dinner", 72),
    ("expense", "Food", 3800, "Coffee & snacks", 68),
    ("expense", "Food", 6900, "Groceries", 60),
    ("expense", "Food", 4400, "Takeout", 55),
    ("expense", "Food", 7300, "Groceries – Whole Foods", 45),
    ("expense", "Food", 5100, "Restaurant lunch", 38),
    ("expense", "Food", 6500, "Groceries", 20),
    ("expense", "Food", 4900, "DoorDash", 10),
    ("expense", "Food", 3200, "Coffee shop", 3),
    # -- Shopping --
    ("expense", "Shopping", 18900, "Amazon haul", 83),
    ("expense", "Shopping", 24500, "Clothing – Zara", 78),
    ("expense", "Shopping", 9800, "Home decor – Target", 71),
    ("expense", "Shopping", 31200, "Electronics – Best Buy", 65),
    ("expense", "Shopping", 14600, "Amazon – household items", 58),
    ("expense", "Shopping", 22000, "Nordstrom sale", 50),
    ("expense", "Shopping", 8700, "Online subscription boxes", 44),
    ("expense", "Shopping", 19500, "Amazon", 35),
    ("expense", "Shopping", 27300, "Furniture – IKEA", 28),
    ("expense", "Shopping", 11200, "Target run", 18),
    ("expense", "Shopping", 16800, "Clothing – H&M", 8),
    ("expense", "Shopping", 7400, "Amazon impulse buy", 2),
    # -- Transport --
    ("expense", "Transport", 8500, "Monthly transit pass", 82),
    ("expense", "Transport", 2300, "Uber rides", 74),
    ("expense", "Transport", 8500, "Monthly transit pass", 52),
    ("expense", "Transport", 3100, "Lyft rides", 42),
    ("expense", "Transport", 8500, "Monthly transit pass", 22),
    ("expense", "Transport", 1900, "Uber", 12),
    # -- Utilities --
    ("expense", "Utilities", 12000, "Electricity & gas", 80),
    ("expense", "Utilities", 8900, "Internet", 78),
    ("expense", "Utilities", 12500, "Electricity & gas", 50),
    ("expense", "Utilities", 8900, "Internet", 48),
    ("expense", "Utilities", 11800, "Electricity & gas", 20),
    ("expense", "Utilities", 8900, "Internet", 18),
    # -- Savings --
    ("investment", "Savings", 20000, "Monthly savings", 82),
    ("investment", "Savings", 20000, "Monthly savings", 52),
    ("investment", "Savings", 20000, "Monthly savings", 22),
]

_SAVVY_INVESTOR_TRANSACTIONS = [
    # -- Income --
    ("income", "Salary", 800000, "Monthly salary", 85),
    ("income", "Salary", 800000, "Monthly salary", 55),
    ("income", "Salary", 800000, "Monthly salary", 25),
    ("income", "Freelance", 150000, "Consulting", 60),
    ("income", "Other", 32000, "Stock dividends", 45),
    ("income", "Other", 28000, "Stock dividends", 15),
    # -- Investments --
    ("investment", "Stocks", 200000, "S&P 500 ETF – VTI", 83),
    ("investment", "Stocks", 150000, "NASDAQ ETF – QQQ", 80),
    ("investment", "Stocks", 100000, "Individual stocks – AAPL", 75),
    ("investment", "Savings", 100000, "High-yield savings", 82),
    ("investment", "Stocks", 200000, "S&P 500 ETF – VTI", 53),
    ("investment", "Stocks", 120000, "Tech ETF", 50),
    ("investment", "Savings", 100000, "High-yield savings", 52),
    ("investment", "Stocks", 80000, "Dividend stocks", 45),
    ("investment", "Stocks", 200000, "S&P 500 ETF – VTI", 23),
    ("investment", "Stocks", 130000, "International ETF", 20),
    ("investment", "Savings", 100000, "High-yield savings", 22),
    ("investment", "Other", 50000, "Crypto – BTC", 40),
    # -- Modest expenses --
    ("expense", "Food", 4500, "Groceries", 79),
    ("expense", "Food", 2800, "Restaurant", 65),
    ("expense", "Food", 4200, "Groceries", 49),
    ("expense", "Food", 3100, "Meal prep delivery", 35),
    ("expense", "Food", 4400, "Groceries", 19),
    ("expense", "Food", 2600, "Coffee & lunch", 6),
    ("expense", "Transport", 8500, "Monthly transit pass", 82),
    ("expense", "Transport", 8500, "Monthly transit pass", 52),
    ("expense", "Transport", 8500, "Monthly transit pass", 22),
    ("expense", "Utilities", 11000, "Electricity & internet", 80),
    ("expense", "Utilities", 11000, "Electricity & internet", 50),
    ("expense", "Utilities", 11000, "Electricity & internet", 20),
    ("expense", "Shopping", 5500, "Books & learning materials", 55),
    ("expense", "Shopping", 3200, "Office supplies", 25),
    # -- Donations --
    ("donation", "Charity", 25000, "Monthly charity donation", 82),
    ("donation", "Charity", 25000, "Monthly charity donation", 52),
    ("donation", "Charity", 25000, "Monthly charity donation", 22),
]

_BUDGET_CONSCIOUS_TRANSACTIONS = [
    # -- Income --
    ("income", "Salary", 320000, "Monthly salary", 85),
    ("income", "Salary", 320000, "Monthly salary", 55),
    ("income", "Salary", 320000, "Monthly salary", 25),
    ("income", "Freelance", 45000, "Freelance writing", 70),
    ("income", "Freelance", 30000, "Weekend gig", 35),
    # -- Food – very controlled --
    ("expense", "Food", 3800, "Groceries – ALDI", 84),
    ("expense", "Food", 2100, "Groceries – ALDI", 77),
    ("expense", "Food", 1200, "Coffee", 72),
    ("expense", "Food", 3500, "Groceries", 63),
    ("expense", "Food", 900, "Snacks", 58),
    ("expense", "Food", 3600, "Groceries – ALDI", 54),
    ("expense", "Food", 1800, "Meal prep ingredients", 45),
    ("expense", "Food", 3400, "Groceries", 33),
    ("expense", "Food", 800, "Coffee – rare treat", 28),
    ("expense", "Food", 3700, "Groceries – ALDI", 23),
    ("expense", "Food", 1100, "Snacks", 15),
    ("expense", "Food", 3300, "Groceries", 5),
    # -- Transport –- minimal --
    ("expense", "Transport", 5500, "Monthly bus pass", 82),
    ("expense", "Transport", 5500, "Monthly bus pass", 52),
    ("expense", "Transport", 5500, "Monthly bus pass", 22),
    ("expense", "Transport", 1200, "Occasional Uber", 60),
    ("expense", "Transport", 800, "Occasional Uber", 30),
    # -- Utilities --
    ("expense", "Utilities", 9500, "Electricity & internet", 80),
    ("expense", "Utilities", 9500, "Electricity & internet", 50),
    ("expense", "Utilities", 9500, "Electricity & internet", 20),
    # -- Shopping – minimal --
    ("expense", "Shopping", 2900, "Household essentials", 75),
    ("expense", "Shopping", 1800, "Cleaning supplies", 40),
    ("expense", "Shopping", 3200, "Household essentials", 10),
    # -- Savings – small but consistent --
    ("investment", "Savings", 30000, "Emergency fund contribution", 83),
    ("investment", "Savings", 30000, "Emergency fund contribution", 53),
    ("investment", "Savings", 30000, "Emergency fund contribution", 23),
    ("investment", "Stocks", 10000, "Low-cost index fund", 78),
    ("investment", "Stocks", 10000, "Low-cost index fund", 48),
    ("investment", "Stocks", 10000, "Low-cost index fund", 18),
]

PROFILES = {
    "frequent_shopper": _FREQUENT_SHOPPER_TRANSACTIONS,
    "savvy_investor": _SAVVY_INVESTOR_TRANSACTIONS,
    "budget_conscious": _BUDGET_CONSCIOUS_TRANSACTIONS,
}

PROFILE_LABELS = {
    "frequent_shopper": "Frequent Shopper",
    "savvy_investor": "Savvy Investor",
    "budget_conscious": "Budget-Conscious Saver",
}


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post("", response_model=DemoLoadResponse)
async def load_demo_profile(
    body: DemoLoadRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Clear the user's existing transactions and load a demo profile.
    Creates a 'Demo Wallet' if none exists. Existing wallets are kept.
    """
    profile_key = body.profile
    if profile_key not in PROFILES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown profile")

    raw_transactions = PROFILES[profile_key]

    # Find or create demo wallet
    wallet_result = await db.execute(
        select(Wallet).where(Wallet.user_id == user_id, Wallet.name == "Demo Wallet")
    )
    wallet = wallet_result.scalar_one_or_none()
    if wallet is None:
        wallet = Wallet(user_id=user_id, name="Demo Wallet")
        db.add(wallet)
        await db.flush()
        await db.refresh(wallet)

    # Delete existing transactions in the demo wallet
    await db.execute(
        delete(Transaction).where(Transaction.wallet_id == wallet.id)
    )

    # Load system subcategories into a lookup map
    sc_result = await db.execute(
        select(Subcategory).where(Subcategory.user_id.is_(None), Subcategory.is_system.is_(True))
    )
    subcategories: dict[tuple[str, str], UUID] = {}
    for sc in sc_result.scalars().all():
        subcategories[(sc.transaction_type.value, sc.name)] = sc.id

    # Insert profile transactions
    inserted = 0
    for tx_type_str, sc_name, amount_cents, description, days_ago in raw_transactions:
        key = (tx_type_str, sc_name)
        sc_id = subcategories.get(key)
        if sc_id is None:
            continue
        tx = Transaction(
            wallet_id=wallet.id,
            type=TransactionTypeEnum(tx_type_str),
            subcategory_id=sc_id,
            amount_cents=amount_cents,
            description=description,
            tags=[],
            transaction_date=_d(days_ago),
        )
        db.add(tx)
        inserted += 1

    await db.commit()

    return DemoLoadResponse(
        profile=profile_key,
        label=PROFILE_LABELS[profile_key],
        transactions_loaded=inserted,
        wallet_id=wallet.id,
    )
