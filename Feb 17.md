## Dalla Docker local run (Feb 17)

- **Prepare env files**
  - `cp backend/.env.example backend/.env` and set Cognito vars (`COGNITO_USER_POOL_ID`, `COGNITO_APP_CLIENT_ID`, optional `COGNITO_REGION`).
  - Optionally set `DATABASE_URL=postgresql+asyncpg://dalla:dalla@db:5432/dalla` for Docker.
  - `cp frontend/.env.example frontend/.env`, set Cognito vars, and for Docker set **`VITE_API_URL=http://localhost:8000`** (browser must call backend via `localhost`, not `backend`).

- **Start stack (db + backend + frontend)**
  - From repo root: `docker compose up --build`

- **Initialize DB schema (first run only)**
  - `docker compose exec backend python -m scripts.create_tables`

- **Access**
  - Backend docs: `http://localhost:8000/docs`
  - Frontend SPA: `http://localhost:5173`

- **Stop everything**
  - `docker compose down`

- **Gotcha: wallets/transactions “Load failed”**
  - **Symptom**: After login, wallets and transactions screens show **“Load failed”** and nothing can be created.
  - **Root cause**: Frontend `VITE_API_URL` pointing at `http://backend:8000` (a Docker-only hostname) instead of `http://localhost:8000`, plus an override in `docker-compose.yml` (`frontend.environment.VITE_API_URL`).
  - **Fix**: Set `VITE_API_URL=http://localhost:8000` in `frontend/.env`, remove the `VITE_API_URL` override from `docker-compose.yml`, then `docker compose down && docker compose build frontend && docker compose up`.

## Deployment decision (cloud)

- **Choice**: Run two Docker images (frontend + backend) on **ECS with Fargate**, and use **RDS** for PostgreSQL. For the first demo we can skip ALB (public IP on services) and add **ALB** later for a cleaner, production-style setup.

- **ECS**: Container orchestration service that runs and manages tasks/services (our frontend and backend containers).
- **Fargate**: Serverless compute for containers; runs ECS tasks without managing EC2 instances.
- **RDS (PostgreSQL)**: Managed relational database replacing the local Postgres container in the cloud.
- **ALB (optional)**: Application Load Balancer that provides a stable HTTPS endpoint and routes traffic to one or more ECS services.
