# Run Dalla locally

Steps to run the full app (backend + frontend) on your machine.

## 1. Database

- Start PostgreSQL (e.g. `brew services start postgresql@14`).
- Create the database:
  ```bash
  createdb dalla
  ```
- Create tables from SQLAlchemy models:
  ```bash
  cd backend
  python -m scripts.create_tables
  ```

## 2. Backend

- In `backend/`: copy `.env.example` to `.env` and set:
  - `DATABASE_URL` — e.g. `postgresql+asyncpg://127.0.0.1/dalla` (use `127.0.0.1` if you get IPv6 connection refused)
  - `COGNITO_USER_POOL_ID` — Cognito user pool ID
  - `COGNITO_APP_CLIENT_ID` — Cognito app client ID
  - `COGNITO_REGION` — e.g. `us-east-1` (optional, default `us-east-1`)
- Install and run:
  ```bash
  cd backend
  pip install -r requirements.txt
  uvicorn app.main:app --reload
  ```
- API: http://localhost:8000 (docs at http://localhost:8000/docs).

## 3. Frontend

- In `frontend/`: copy `.env.example` to `.env` and set (use the same Cognito User Pool and App Client as the backend):
  - `VITE_API_URL` — use `/api` in development (Vite proxies to the backend)
  - `VITE_COGNITO_USER_POOL_ID`
  - `VITE_COGNITO_APP_CLIENT_ID`
  - `VITE_COGNITO_REGION` — e.g. `us-east-1`
- Install and run:
  ```bash
  cd frontend
  npm install
  npm run dev
  ```
- App: http://localhost:5173 (Vite proxies `/api` to the backend).

## 4. Use the app

Open the app in the browser and sign in with Cognito. The app calls `PUT /users/me` to create or update your user. Without valid Cognito config in both `.env` files, the app shows “Auth not configured” and will not render the sign-in UI.

---

## 5. Run everything with Docker

You can also run PostgreSQL, the backend, and the frontend together using Docker Compose.

1. **Prepare environment files**

   - In `backend/`:
     ```bash
     cd backend
     cp .env.example .env
     ```
     - Set `COGNITO_USER_POOL_ID`, `COGNITO_APP_CLIENT_ID`, and (optionally) `COGNITO_REGION`.
     - You can keep the default host-based `DATABASE_URL` or use the Docker-friendly example from `.env.example`:
       - `DATABASE_URL=postgresql+asyncpg://dalla:dalla@db:5432/dalla`

   - In `frontend/`:
     ```bash
     cd frontend
     cp .env.example .env
     ```
     - Set the Cognito variables.
     - For Docker, set:
       - `VITE_API_URL=http://backend:8000`

2. **Build and start all services**

   From the repo root:

   ```bash
   docker compose up --build
   ```

   This starts:

   - `db` — PostgreSQL (database `dalla`, user `dalla`, password `dalla`)
   - `backend` — FastAPI API on `http://localhost:8000`
   - `frontend` — Vite dev server on `http://localhost:5173`

3. **Create tables in the Docker database (first run)**

   Once containers are up, run:

   ```bash
   docker compose exec backend python -m scripts.create_tables
   ```

4. **Use the app**

   - Backend API/docs: http://localhost:8000/docs
   - Frontend app: http://localhost:5173

5. **Stop containers**

   ```bash
   docker compose down
   ```

For more details on the backend and frontend, including non-Docker setup, see `backend/README.md` and `frontend/README.md`.
