# Why FastAPI Replaces API Gateway's Core Features

## What API Gateway gives you

API Gateway is a managed layer that sits in front of your backend and handles:

- **Request validation** — reject malformed payloads before they reach your app
- **Auth enforcement** — verify tokens, block unauthenticated requests
- **Rate limiting** — block users sending too many requests per second
- **Routing** — send `/users` to one function, `/transactions` to another

For a Lambda backend, you need all of this because Lambda functions are just plain Python — they have no HTTP server, no routing, no built-in validation.

For a FastAPI backend, most of this is already built in.

---

## How FastAPI handles each one

### Request validation — Pydantic

Every route in FastAPI declares what shape the request body must be, using a Pydantic model:

```python
class TransactionCreate(BaseModel):
    amount: float
    category: str
    wallet_id: int
    date: date

@router.post("/transactions")
async def create_transaction(body: TransactionCreate):
    ...
```

FastAPI automatically:
- Parses the incoming JSON
- Checks every field is present and the right type
- Returns a `422 Unprocessable Entity` with a detailed error message if anything is wrong

This happens before your function body even runs. You never write manual `if "amount" not in body` checks.

### Auth enforcement — Cognito JWT middleware

Every protected route uses a dependency that validates the Cognito JWT:

```python
@router.get("/wallets")
async def get_wallets(user=Depends(get_current_user)):
    ...
```

`get_current_user` decodes and verifies the token on every request. If it's missing, expired, or tampered with, FastAPI returns a `401` before the handler runs. API Gateway's Cognito authorizer would do the exact same check — just at an earlier hop.

### Routing

FastAPI's router handles this natively:

```python
app.include_router(transactions.router, prefix="/transactions")
app.include_router(wallets.router, prefix="/wallets")
app.include_router(chat.router, prefix="/chat")
```

Each prefix maps to a different file of route handlers. No API Gateway routing config needed.

---

## What API Gateway adds that FastAPI doesn't

- **Rate limiting at the infrastructure level** — FastAPI has no built-in rate limiter. You'd need a library (e.g. `slowapi`) or a reverse proxy (Nginx) to do this. API Gateway does it natively.
- **Usage plans and API keys** — useful if you're exposing the API to external third-party developers with different tiers.
- **DDoS protection** — API Gateway integrates with AWS Shield.

For coinBaby — a private app used only by its own frontend — none of these matter. There are no third-party consumers, and the user base is small enough that rate limiting is not a concern.

---

## Summary

| Feature | API Gateway | FastAPI |
|---|---|---|
| Request validation | Schema-based, configured separately | Pydantic, declared in code |
| Auth | Cognito authorizer, configured separately | JWT dependency, declared in code |
| Routing | Configured in console/Terraform | `include_router`, declared in code |
| Rate limiting | Built-in | Needs extra library |
| Cost | Per-request billing | Free (runs on EC2 you already pay for) |

For a backend that already does validation and auth in code, API Gateway adds an extra network hop and billing with no functional benefit.
