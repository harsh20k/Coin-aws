# Dalla API (FastAPI)

REST API for the Dalla finance app. Uses PostgreSQL and Cognito JWT auth.

## Setup

1. Create a PostgreSQL database and run the schema (see `../notes/schema.md` or the SQL in the project docs).
2. Copy `.env.example` to `.env` and set:
   - `DATABASE_URL` — e.g. `postgresql+asyncpg://user:pass@localhost:5432/dalla`
   - `COGNITO_USER_POOL_ID` — Cognito user pool ID
   - `COGNITO_APP_CLIENT_ID` — Cognito app client ID
   - `COGNITO_REGION` — e.g. `us-east-1` (optional, default `us-east-1`)
3. Install and run:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs

## Auth

All endpoints except `GET /health` and (for first-time users) `PUT /users/me` require a valid Cognito JWT in the `Authorization: Bearer <token>` header. After sign-in, call `PUT /users/me` to create or update the app user; then use `get_current_user_id` for all other routes.

## Endpoints

- `GET/PUT /users/me` — Current user (get or upsert by Cognito `sub`)
- `GET/POST /wallets`, `GET/PUT/DELETE /wallets/{id}`
- `GET /subcategories?type=...`, `POST /subcategories`, `PUT/DELETE /subcategories/{id}`
- `GET /transactions?wallet_id=&type=&date_from=&date_to=`, `POST /transactions`, `GET/PUT/DELETE /transactions/{id}`
- `GET /budgets?period_start=&period_end=`, `POST /budgets`, `GET/PUT/DELETE /budgets/{id}`
- `GET /goals?period_start=&period_end=`, `POST /goals`, `GET/PUT/DELETE /goals/{id}`
- `POST /chat` — Stub; body `{"message": "..."}`, returns placeholder reply (wire to Bedrock later).
