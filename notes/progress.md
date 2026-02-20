# Dalla – progress

**Last updated:** Feb 20, 2025

## Current state

- **Auth:** Sign up/login with Cognito work locally; backend validates JWT and `PUT /users/me` links app user to `cognito_sub`. Cloud Cognito is provisioned via Terraform; not yet E2E tested through CloudFront.
- **Backend:** FastAPI + async Postgres via SQLAlchemy; health at `GET /health`; domain routers for users, wallets, transactions, subcategories, budgets, goals, chat. Works locally; on AWS the blocker is 502.
- **Frontend:** React + Vite SPA with auth guard and API client. Local Docker/Docker Compose in `Feb 17.md`. Cloud path: build with `VITE_API_URL`, sync `dist/` to S3, invalidate CloudFront — not yet smoke-tested.
- **Infra (Terraform):** `infra/terraform/` provisions VPC, RDS, Cognito, ECR, backend EC2 + ALB, S3 + CloudFront, SSM. Terraform apply has succeeded; IAM prereqs in `Deploy-AWS.md`.
- **Cloud issue:** ALB returns **502 Bad Gateway** for the API. See `Feb 19.md` for debug (target health, container/user_data, SSM, DB). **Option:** remove ALB and expose backend via EC2 public IP/Elastic IP (simpler, no HTTPS at edge unless added on EC2).
- **Local run:** `Deploy-local.md` (bare metal), `Feb 17.md` (Docker Compose).

### AWS services in use

| Area | Services |
|------|----------|
| **Backend** | VPC, subnets, SGs; RDS (Postgres); EC2; ALB + target group + listener; ECR; SSM; CloudWatch Logs; IAM (instance role, Terraform user) |
| **Frontend** | S3 (static bucket), CloudFront; Cognito (shared with backend) |

## Remaining steps

1. **Apply Terraform & verify backend** – Run `terraform apply`, grab `api_url`/`backend_public_ip`, and confirm `GET /health` returns 200 from the EIP/Route53 URL.
2. **DB schema in RDS** – Use `DATABASE_URL` (Terraform output or SSM) to run the table-creation/migration script once against the cloud Postgres.
3. **Deploy & smoke-test frontend** – Build with `VITE_API_URL` set to the cloud API URL, sync `dist/` to the frontend S3 bucket, invalidate CloudFront, and test login + one full flow.
4. **AI conversation** – Wire the Chat page to Bedrock (or chosen service) and scope answers to the user’s wallets, transactions, budgets, and goals.
5. **Core product flows** – Verify create/edit/delete for wallets, transactions, budgets, goals (and subcategories) end-to-end in the cloud environment.
6. **Subcategories UX** – Seed default subcategories and expose subcategory management in the UI.
7. **Project polish** – Confirm AWS Academy requirements, architecture diagram + report notes, basic logging/alarms if needed.

