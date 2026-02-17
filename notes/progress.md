# Dalla – progress

## Current state

- **Auth:** Sign up and login with Cognito work locally. Frontend uses Amplify; backend validates JWT and `PUT /users/me` creates/updates the app user linked to `cognito_sub`.
- **Backend:** FastAPI, PostgreSQL (async), SQLAlchemy. Routers: users, wallets, transactions, subcategories, budgets, goals, chat. Tables match [schema.md](schema.md).
- **Frontend:** React + Vite. Pages: Dashboard, Wallets, Transactions, Budgets, Goals, Chat. Auth guard and API client wired.
- **Infra:** Terraform in `infra/terraform/` provisions Cognito user pool + app client only.
- **Local run:** See [Deploy-local.md](Deploy-local.md) — Postgres, backend and frontend `.env`, then `uvicorn` + `npm run dev`.

## Remaining steps

1. **Containerize** – Add Dockerfiles for backend and frontend; Docker Compose for local (db + backend + frontend).
2. **Deploy to AWS** – Terraform: VPC, RDS, ECR, ECS (Fargate), ALB. Optional: CodePipeline/CodeBuild for deploy on push.
3. **AI conversation** – Wire Chat to Bedrock; scope answers to user’s wallets, transactions, budgets, goals.
4. **Core flows** – Create/edit/delete for wallets, transactions, budgets, goals (and subcategories) end-to-end.
5. **Subcategories** – Seed defaults per transaction type; allow user-defined subcategories.
6. **Project requirements** – At least one from Compute, Storage, Networking, Database; IaC; AWS Academy–friendly.
