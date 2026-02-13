# Dalla API (FastAPI)

REST API for the Dalla finance app. Uses PostgreSQL and Cognito JWT auth.

## Setup

1. Start PostgreSQL (e.g. `brew services start postgresql@14`).
2. Create the database. On Homebrew PostgreSQL the default superuser is your macOS user, not `postgres`:

   ```bash
   createdb dalla
   # or: psql -d postgres -c "CREATE DATABASE dalla;"
   ```

3. Create tables from SQLAlchemy models (no need to run SQL by hand):

   ```bash
   cd backend
   python -m scripts.create_tables
   ```

4. Copy `.env.example` to `.env` and set:
   - `DATABASE_URL` — e.g. `postgresql+asyncpg://localhost/dalla` (use `127.0.0.1` if you get IPv6 connection refused)
   - `COGNITO_USER_POOL_ID` — Cognito user pool ID
   - `COGNITO_APP_CLIENT_ID` — Cognito app client ID
   - `COGNITO_REGION` — e.g. `us-east-1` (optional, default `us-east-1`)
5. Install and run:

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

## Tests

Uses pytest and pytest-asyncio. Auth is overridden so no real Cognito is needed; a test user is created per run.

- PostgreSQL must be running and `DATABASE_URL` must point to an existing DB (e.g. `dalla`); run `python -m scripts.create_tables` if tables don’t exist yet.
- Install deps in the same env you use for pytest: `pip install -r requirements.txt` (so `python-jose` etc. are available).

```bash
cd backend
pytest
```

Run with verbose: `pytest -v`
