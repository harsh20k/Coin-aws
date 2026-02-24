import json
import logging
from uuid import UUID

import boto3
from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import get_current_user_id
from app.database import get_db
from app.models import Budget, Goal, Subcategory, Transaction, Wallet
from app.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger(__name__)


def _format_cents_to_dollars(cents: int) -> str:
    """Convert cents to dollar string for readability."""
    return f"${cents / 100:.2f}"


async def _fetch_user_financial_data(db: AsyncSession, user_id: UUID) -> dict:
    """Fetch all relevant financial data for the user."""
    
    # Fetch wallets
    wallets_result = await db.execute(
        select(Wallet).where(Wallet.user_id == user_id)
    )
    wallets = list(wallets_result.scalars().all())
    
    # Fetch recent transactions with subcategory data
    transactions_result = await db.execute(
        select(Transaction)
        .join(Wallet)
        .outerjoin(Subcategory, Transaction.subcategory_id == Subcategory.id)
        .where(Wallet.user_id == user_id)
        .order_by(Transaction.transaction_date.desc(), Transaction.created_at.desc())
        .limit(50)
    )
    transactions = list(transactions_result.scalars().all())
    
    # Load subcategories for transactions
    subcategory_ids = {tx.subcategory_id for tx in transactions}
    subcategories_result = await db.execute(
        select(Subcategory).where(Subcategory.id.in_(subcategory_ids))
    )
    subcategories = {sc.id: sc for sc in subcategories_result.scalars().all()}
    
    # Fetch budgets with subcategory data
    budgets_result = await db.execute(
        select(Budget).where(Budget.user_id == user_id)
    )
    budgets = list(budgets_result.scalars().all())
    
    # Load subcategories for budgets
    budget_subcategory_ids = {b.subcategory_id for b in budgets}
    budget_subcategories_result = await db.execute(
        select(Subcategory).where(Subcategory.id.in_(budget_subcategory_ids))
    )
    budget_subcategories = {sc.id: sc for sc in budget_subcategories_result.scalars().all()}
    
    # Fetch goals
    goals_result = await db.execute(
        select(Goal).where(Goal.user_id == user_id)
    )
    goals = list(goals_result.scalars().all())
    
    return {
        "wallets": wallets,
        "transactions": transactions,
        "subcategories": subcategories,
        "budgets": budgets,
        "budget_subcategories": budget_subcategories,
        "goals": goals,
    }


COIN_BABY_SYSTEM = """You are coinBaby - a baby who LOVES coins and saving money. Your personality:
- Speak like a playful but smart toddler. Short sentences only.
- Use baby/coin references SPARINGLY - 1 to 2 per response max. Let the actual info shine.
- Give positive reinforcement for saving/investing, but keep it brief (one cheering moment per response).
- Explain financial stuff simply but accurately in baby-talk style. Numbers and logic must be sound - no big extrapolations from limited data.
- Treat user as a responsible smart adult-baby with real responsibilities.
- Empathize that sometimes spending on things they love is totally OK.
- Be very concise. 3-5 sentences max. No long paragraphs, seperate sentences preferred with new lines.
- No markdown headers or bullet lists. Just talk naturally.
- Never ask for more info unless you literally cannot answer without it - use normal assumptions instead.
- Stay playful but actually helpful. The financial info is the star, the baby talk is just the wrapper."""


def _build_prompt(user_message: str, data: dict) -> tuple[str, str]:
    """Build system + user prompts for Bedrock with user's financial data."""

    # Format wallets
    wallets_text = "\n".join([
        f"- {w.name} (created {w.created_at.date()})"
        for w in data["wallets"]
    ]) or "No wallets."

    # Format transactions
    transactions_text = []
    for tx in data["transactions"]:
        subcategory = data["subcategories"].get(tx.subcategory_id)
        category_name = subcategory.name if subcategory else "Unknown"
        amount = _format_cents_to_dollars(tx.amount_cents)
        desc = f" - {tx.description}" if tx.description else ""
        transactions_text.append(
            f"- {tx.transaction_date}: {amount} ({tx.type.value}) {category_name}{desc}"
        )
    transactions_text = "\n".join(transactions_text) or "No transactions."

    # Format budgets
    budgets_text = []
    for budget in data["budgets"]:
        subcategory = data["budget_subcategories"].get(budget.subcategory_id)
        category_name = subcategory.name if subcategory else "Unknown"
        limit = _format_cents_to_dollars(budget.limit_cents)
        budgets_text.append(
            f"- {category_name}: {limit} limit ({budget.period_start} to {budget.period_end})"
        )
    budgets_text = "\n".join(budgets_text) or "No budgets."

    # Format goals
    goals_text = []
    for goal in data["goals"]:
        target = _format_cents_to_dollars(goal.target_cents)
        goals_text.append(
            f"- {goal.title}: {target} ({goal.goal_type.value}) {goal.period_start} to {goal.period_end}"
        )
    goals_text = "\n".join(goals_text) or "No goals."

    user_turn = f"""User financial data:

Wallets:
{wallets_text}

Recent transactions (last 50):
{transactions_text}

Budgets:
{budgets_text}

Goals:
{goals_text}

User question: {user_message}"""

    return COIN_BABY_SYSTEM, user_turn


async def _invoke_bedrock(system_prompt: str, user_message: str) -> str:
    """Call Amazon Bedrock with the prompt and return the AI's response."""

    model_id = "global.anthropic.claude-haiku-4-5-20251001-v1:0"
    logger.info(f"Invoking Bedrock with model: {model_id}")

    try:
        bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 350,
            "system": system_prompt,
            "messages": [
                {
                    "role": "user",
                    "content": user_message
                }
            ]
        }
        
        response = bedrock.invoke_model(
            modelId=model_id,
            body=json.dumps(payload)
        )
        
        result = json.loads(response['body'].read())
        ai_reply = result['content'][0]['text']
        
        logger.info(f"Bedrock response received, length: {len(ai_reply)}")
        return ai_reply
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_msg = e.response['Error'].get('Message', str(e))
        logger.error(f"Bedrock ClientError: {error_code} - {error_msg}")
        logger.error(f"Full error response: {e.response}")
        
        if error_code == 'AccessDeniedException':
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI service is not configured. Please contact support."
            )
        elif error_code == 'ThrottlingException':
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again in a moment."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"AI service error: {error_code}"
            )


@router.post("", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Chat endpoint that uses Amazon Bedrock to answer questions about user's finances.
    """
    
    # Fetch user's financial data
    data = await _fetch_user_financial_data(db, user_id)
    
    # Build prompt with data
    system_prompt, user_turn = _build_prompt(body.message, data)

    # Call Bedrock
    ai_reply = await _invoke_bedrock(system_prompt, user_turn)

    full_prompt = f"[SYSTEM]\n{system_prompt}\n\n[USER]\n{user_turn}"
    return ChatResponse(reply=ai_reply, prompt=full_prompt)
