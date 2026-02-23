# Dalla – progress

**Last updated:** Feb 22, 2026

## Current state

- **Auth:** Sign up/login with Cognito. Backend validates JWT; `PUT /users/me` links app user to `cognito_sub`. E2E works via CloudFront when using the HTTP frontend URL (mixed-content workaround).
- **Backend:** FastAPI + async Postgres (SQLAlchemy). Health at `GET /health`; routers for users, wallets, transactions, subcategories, budgets, goals, chat. On AWS: EC2 + EIP. DB tables via `scripts.create_tables`; seed defaults on startup. **CI/CD:** CodeCommit → CodePipeline (BuildBackend → DeployBackend via SSM Run Command → BuildFrontend). Backend Dockerfile uses ECR Public base (`public.ecr.aws/docker/library/python:3.12-slim`) to avoid Docker Hub rate limit. EC2 user_data includes ECR login before first-boot `docker run`.
- **Frontend:** React + Vite SPA; auth guard and API client. Build with `VITE_API_URL` + Cognito env, sync `dist/` to S3, invalidate CloudFront. Smoke-tested via **http://**&lt;cloudfront-domain&gt;.
- **Infra (Terraform):** `infra/terraform/` — VPC, RDS, Cognito, ECR, backend EC2 + EIP, S3 + CloudFront, SSM, CodeCommit, CodeBuild, CodePipeline. Full deploy in `Deploy-AWS.md`. CloudFront `viewer_protocol_policy = "allow-all"` for HTTP app + backend.
- **Local run:** `Deploy-local.md`, `Feb 17.md` (Docker Compose).

### AWS services in use

| Area | Services |
|------|----------|
| **Backend** | VPC, RDS, EC2 + EIP, ECR, SSM, CloudWatch Logs, IAM (instance + Terraform user) |
| **Frontend** | S3, CloudFront, Cognito |
| **CI/CD** | CodeCommit, CodeBuild, CodePipeline, S3 artifacts |

## Remaining steps

1. **Apply EC2 user_data fix (if not done)** — `terraform apply` so new instances get ECR login in user_data; or fix existing instance via SSH (ECR login + docker pull/run) or replace instance.
2. **Smoke-test full E2E in cloud** — Backend `GET /health` via api_url; open app at **http://**&lt;cloudfront-domain&gt;; sign in; confirm one flow (e.g. Wallets or transactions).
3. **DB schema (if new stack)** — After fresh apply, run table creation (SSH + `docker exec` or one-off container; see `Deploy-AWS.md` §4).
4. **HTTPS for API (later)** — Serve API over HTTPS (e.g. ALB + ACM or CloudFront origin) so frontend can use redirect-to-HTTPS safely.
5. **AI / Chat** — Wire Chat page to Bedrock (or chosen service); scope answers to user’s wallets, transactions, budgets, goals.
6. **Core flows E2E** — Verify create/edit/delete for wallets, transactions, budgets, goals (and subcategories) in the cloud UI.
7. **Subcategories UX** — Seed default subcategories; expose subcategory management in the UI.
8. **Project polish** — AWS Academy requirements, architecture diagram/report, logging/alarms as needed.
