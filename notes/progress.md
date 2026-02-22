# Dalla – progress

**Last updated:** Feb 20, 2025

## Current state

- **Auth:** Sign up/login with Cognito. Backend validates JWT; `PUT /users/me` links app user to `cognito_sub`. E2E works via CloudFront when using the HTTP frontend URL (mixed-content workaround).
- **Backend:** FastAPI + async Postgres (SQLAlchemy). Health at `GET /health`; routers for users, wallets, transactions, subcategories, budgets, goals, chat. On AWS: reachable via **EC2 Elastic IP** (ALB removed). DB tables via `scripts.create_tables`; seed defaults on startup.
- **Frontend:** React + Vite SPA; auth guard and API client. Build with `VITE_API_URL` + Cognito env, sync `dist/` to S3, invalidate CloudFront. Smoke-tested via **http://**&lt;cloudfront-domain&gt; (see caveats below).
- **Infra (Terraform):** `infra/terraform/` — VPC, RDS, Cognito, ECR, backend EC2 + EIP, S3 + CloudFront, SSM. Full deploy steps in `Deploy-AWS.md`. RDS master password uses `override_special` (no `/`, `@`, `"`, space). CloudFront `viewer_protocol_policy = "allow-all"` so app can be opened over HTTP and call the HTTP backend without mixed-content blocking.
- **Local run:** `Deploy-local.md` (bare metal), `Feb 17.md` (Docker Compose).

### AWS services in use

| Area | Services |
|------|----------|
| **Backend** | VPC, subnets, SGs; RDS (Postgres); EC2 + EIP; ECR; SSM; CloudWatch Logs; IAM (instance role, Terraform user) |
| **Frontend** | S3 (static bucket), CloudFront; Cognito (shared with backend) |

## Remaining steps

1. **Smoke-test full E2E in cloud** – Backend `GET /health` via `api_url`; open app at **http://**&lt;cloudfront-domain&gt;; sign in; confirm one flow (e.g. Wallets or transactions).
2. **DB schema (if new stack)** – After fresh `terraform apply`, run table creation (SSH + `docker exec backend python -m scripts.create_tables` or one-off container; see `Deploy-AWS.md` §4).
3. **HTTPS for API (later)** – Serve API over HTTPS (e.g. ALB + ACM or CloudFront origin to backend) so frontend can use `redirect-to-https` safely.
4. **AI / Chat** – Wire Chat page to Bedrock (or chosen service); scope answers to user’s wallets, transactions, budgets, goals.
5. **Core flows E2E** – Verify create/edit/delete for wallets, transactions, budgets, goals (and subcategories) in the cloud UI.
6. **Subcategories UX** – Seed default subcategories; expose subcategory management in the UI.
7. **Project polish** – AWS Academy requirements, architecture diagram/report, logging/alarms as needed.
