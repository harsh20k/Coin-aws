import json
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


def _build_prompt(user_message: str, data: dict) -> str:
    """Build a prompt for Bedrock with user's financial data."""
    
    # Format wallets
    wallets_text = "\n".join([
        f"- {w.name} (created {w.created_at.date()})"
        for w in data["wallets"]
    ]) or "No wallets found."
    
    # Format transactions
    transactions_text = []
    for tx in data["transactions"]:
        subcategory = data["subcategories"].get(tx.subcategory_id)
        category_name = subcategory.name if subcategory else "Unknown"
        amount = _format_cents_to_dollars(tx.amount_cents)
        desc = f" - {tx.description}" if tx.description else ""
        transactions_text.append(
            f"- {tx.transaction_date}: {amount} ({tx.type.value}) in {category_name}{desc}"
        )
    transactions_text = "\n".join(transactions_text) or "No recent transactions."
    
    # Format budgets
    budgets_text = []
    for budget in data["budgets"]:
        subcategory = data["budget_subcategories"].get(budget.subcategory_id)
        category_name = subcategory.name if subcategory else "Unknown"
        limit = _format_cents_to_dollars(budget.limit_cents)
        budgets_text.append(
            f"- {category_name}: {limit} limit (from {budget.period_start} to {budget.period_end})"
        )
    budgets_text = "\n".join(budgets_text) or "No budgets set."
    
    # Format goals
    goals_text = []
    for goal in data["goals"]:
        target = _format_cents_to_dollars(goal.target_cents)
        goals_text.append(
            f"- {goal.title}: {target} target ({goal.goal_type.value}) from {goal.period_start} to {goal.period_end}"
        )
    goals_text = "\n".join(goals_text) or "No goals set."
    
    # Construct full prompt
    prompt = f"""You are a helpful financial assistant. The user has asked a question about their finances.

User's Financial Data:

Wallets:
{wallets_text}

Recent Transactions (last 50):
{transactions_text}

Budgets:
{budgets_text}

Goals:
{goals_text}

User Question: {user_message}

Please provide a helpful, concise answer based on the data above. If the data doesn't contain enough information to answer the question, say so politely."""
    
    return prompt


async def _invoke_bedrock(prompt: str) -> str:
    """Call Amazon Bedrock with the prompt and return the AI's response."""
    
    try:
        bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
        
        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 500,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        response = bedrock.invoke_model(
            modelId="anthropic.claude-3-haiku-20240307-v1:0",
            body=json.dumps(payload)
        )
        
        result = json.loads(response['body'].read())
        ai_reply = result['content'][0]['text']
        
        return ai_reply
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        # region:debug-ef78fc
        import time, json as _json
        _log = {"sessionId": "ef78fc", "hypothesisId": "H-A/B/C/D/E", "location": "chat.py:_invoke_bedrock", "message": "Bedrock ClientError", "data": {"error_code": error_code, "error_message": str(e), "full_response": str(e.response)}, "timestamp": int(time.time() * 1000)}
        open("/Users/harsh/Artifacts/Dalla/.cursor/debug-ef78fc.log", "a").write(_json.dumps(_log) + "\n")
        # endregion
        if error_code == 'AccessDeniedException':
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI service is not configured. Please contact support."
            )
        elif error_code == 'ThrottlingException':
            # region:debug-ef78fc
            import time as _time3, json as _json3
            _log3 = {"sessionId": "ef78fc", "hypothesisId": "H-G", "location": "chat.py:_invoke_bedrock:throttle", "message": "Bedrock throttling detected", "data": {"error_code": error_code, "error_message": str(e)}, "timestamp": int(_time3.time() * 1000)}
            open("/Users/harsh/Artifacts/Dalla/.cursor/debug-ef78fc.log", "a").write(_json3.dumps(_log3) + "\n")
            # endregion
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
    prompt = _build_prompt(body.message, data)
    
    # Call Bedrock
    ai_reply = await _invoke_bedrock(prompt)
    
    return ChatResponse(reply=ai_reply, prompt=prompt)
