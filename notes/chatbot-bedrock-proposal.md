Here's the minimal approach to get a working prototype:

## 1. Infrastructure Changes (Terraform)

**Add Bedrock permissions to EC2 instance role** in `infra/terraform/ec2.tf`:

```terraform
# Add to the existing instance role policy
statement {
  sid    = "BedrockAccess"
  effect = "Allow"
  actions = [
    "bedrock:InvokeModel"
  ]
  resources = [
    "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-haiku-20240307-v1:0"
  ]
}
```

## 2. Backend Dependencies

Add to `backend/requirements.txt`:
```
boto3>=1.34.0
```

## 3. Implement Chat Endpoint

Update `backend/app/routers/chat.py`:

```python
import json
import boto3
from sqlalchemy import select
from app.database import get_session
from app.models import Transaction, Budget, Goal, Wallet

@router.post("", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    user_id: UUID = Depends(get_current_user_id),
):
    # 1. Fetch user's financial data
    async with get_session() as session:
        # Get recent transactions
        transactions = await session.execute(
            select(Transaction)
            .where(Transaction.user_id == user_id)
            .order_by(Transaction.date.desc())
            .limit(50)
        )
        txns = transactions.scalars().all()
        
        # Get budgets
        budgets = await session.execute(
            select(Budget).where(Budget.user_id == user_id)
        )
        user_budgets = budgets.scalars().all()
        
        # Get wallets
        wallets = await session.execute(
            select(Wallet).where(Wallet.user_id == user_id)
        )
        user_wallets = wallets.scalars().all()
    
    # 2. Build context for AI
    context = f"""
User's Financial Data:

Wallets:
{chr(10).join([f"- {w.name}: ${w.balance}" for w in user_wallets])}

Recent Transactions (last 50):
{chr(10).join([f"- {t.date}: ${t.amount} on {t.description} (category: {t.subcategory_id})" for t in txns])}

Budgets:
{chr(10).join([f"- {b.name}: ${b.amount_limit} per {b.period}" for b in user_budgets])}

User Question: {body.message}

Provide a helpful, concise answer based on the data above.
"""
    
    # 3. Call Bedrock
    bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
    
    payload = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 500,
        "messages": [
            {
                "role": "user",
                "content": context
            }
        ]
    }
    
    response = bedrock.invoke_model(
        modelId="anthropic.claude-3-haiku-20240307-v1:0",
        body=json.dumps(payload)
    )
    
    result = json.loads(response['body'].read())
    ai_reply = result['content'][0]['text']
    
    return ChatResponse(reply=ai_reply)
```

## 4. Deploy

```bash
# Run terraform to add IAM permissions
cd infra/terraform
terraform apply

# Push code - pipeline will deploy
git add .
git commit -m "Add Bedrock chat integration"
git push
```

## 5. Test

```bash
curl -X POST https://your-api.com/chat \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"message": "What did I spend money on recently?"}'
```

---

## What This Does:
1. ✅ Fetches user's transactions, budgets, wallets from PostgreSQL
2. ✅ Constructs a simple prompt with all the data
3. ✅ Sends to Claude 3 Haiku (cheapest, fastest)
4. ✅ Returns AI-generated response

## Limitations of This Prototype:
- No conversation history (each request is independent)
- Dumps ALL data in prompt (inefficient for many transactions)
- No error handling
- Basic prompt (no sophisticated reasoning instructions)

## Next Steps for Production:
- Add conversation history (store in RDS)
- Smart data filtering (only relevant transactions)
- Better prompt engineering
- Streaming responses
- Error handling & fallbacks
- Cost monitoring

This gets you a working chatbot in ~50 lines of code. Want me to explain any part in more detail?