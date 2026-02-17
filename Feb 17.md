## Dalla Docker local run (Feb 17)

- **Prepare env files**
  - `cp backend/.env.example backend/.env` and set Cognito vars (`COGNITO_USER_POOL_ID`, `COGNITO_APP_CLIENT_ID`, optional `COGNITO_REGION`).
  - Optionally set `DATABASE_URL=postgresql+asyncpg://dalla:dalla@db:5432/dalla` for Docker.
  - `cp frontend/.env.example frontend/.env`, set Cognito vars, and for Docker set `VITE_API_URL=http://backend:8000`.

- **Start stack (db + backend + frontend)**
  - From repo root: `docker compose up --build`

- **Initialize DB schema (first run only)**
  - `docker compose exec backend python -m scripts.create_tables`

- **Access**
  - Backend docs: `http://localhost:8000/docs`
  - Frontend SPA: `http://localhost:5173`

- **Stop everything**
  - `docker compose down`

