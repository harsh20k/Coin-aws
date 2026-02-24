# Dalla – progress

**Last updated:** Feb 24, 2026

## Current state

- **Auth:** Cognito sign up/login. Pre Sign-Up Lambda (`lambda/auto_confirm.zip`) auto-confirms users — no email verification needed, users can log in immediately after sign up. Backend validates JWT; `PUT /users/me` links app user to `cognito_sub`.
- **Chat (AI):** Working. `POST /chat` fetches user's wallets, transactions, budgets, goals → builds prompt → calls Bedrock (`global.anthropic.claude-haiku-4-5-20251001-v1:0`). AI persona is **Penny** (coinBaby), a playful toddler who loves coins. Dashboard has inline chat panel. Claude 3.5+ requires inference profile IDs and wildcard region in IAM.
- **Backend:** FastAPI + async Postgres (SQLAlchemy). Routers: users, wallets, transactions, subcategories, budgets, goals, chat, demo. On AWS: EC2 + EIP. CI/CD: CodeCommit → CodePipeline (build + deploy via SSM).
- **Frontend:** React + Vite SPA. 3-column Dashboard (wallets/goals/budgets left, Penny chat center, recent transactions right). Auth guard + API client. Deployed via S3 + CloudFront.
- **Infra (Terraform):** `infra/terraform/` — VPC, RDS, Cognito + Lambda trigger, ECR, EC2 + EIP, S3 + CloudFront, SSM, CodePipeline. EBS volume: 20GB gp3.
- **Branding:** App title = `coinBaby`, header = `coinBaby`, chat agent = `👶 Penny`.

### AWS services in use

| Area | Services |
|------|----------|
| **Backend** | VPC, RDS, EC2 + EIP, ECR, SSM, CloudWatch Logs, IAM |
| **Frontend** | S3, CloudFront, Cognito |
| **AI** | Bedrock (Claude Haiku via inference profile) |
| **Auth** | Cognito User Pool + Pre Sign-Up Lambda |
| **CI/CD** | CodeCommit, CodeBuild, CodePipeline, S3 artifacts |

## Remaining steps

1. **Deploy Lambda + apply Terraform** — `terraform apply` to create the auto-confirm Lambda, IAM role, and wire it to the Cognito user pool. Confirm sign-up works without email verification.
2. **Smoke-test E2E in cloud** — Sign up fresh account, log in immediately, use chat, verify wallets/transactions/budgets/goals all load.
3. **Git cleanup** — `git rm -r --cached backend/app/__pycache__ backend/app/routers/__pycache__` to stop tracking compiled files.
4. **Architecture diagram** — Update/finalize diagram to include Bedrock + Lambda for report/submission.
5. **Project polish** — AWS Academy requirements checklist, final report, logging/alarms if needed.
