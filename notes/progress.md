# Dalla – progress

**Last updated:** Feb 24, 2026 (end of day)

## Current state

- **Live:** [http://coinbaby.click](http://coinbaby.click)
- **Auth:** Cognito sign up/login. Pre Sign-Up Lambda auto-confirms users — no email verification. Backend validates JWT; `PUT /users/me` links app user to `cognito_sub`.
- **Chat (AI):** Working. `POST /chat` fetches user's wallets, transactions, budgets, goals → builds prompt → calls Bedrock (Claude 3.5 Haiku via inference profile `us.anthropic.claude-3-5-haiku-20241022-v1:0`). AI persona is **Penny**, a playful toddler who loves coins. Dashboard has inline chat panel with quick-question templates.
- **Backend:** FastAPI + async Postgres (SQLAlchemy). Routers: users, wallets, transactions, subcategories, budgets, goals, chat, demo. On AWS: EC2 `t3.micro` + EIP, 20GB gp3 EBS. CI/CD: CodeCommit → CodePipeline (build + deploy via SSM).
- **Frontend:** React + Vite SPA. 3-column Dashboard (wallets/goals/budgets left, Penny chat center, recent transactions right). Auth guard + API client. Deployed via S3 + CloudFront. Custom domain `coinbaby.click` via Route 53 + ACM.
- **Infra (Terraform):** `infra/terraform/` — VPC, RDS, Cognito + Lambda trigger, ECR, EC2 + EIP, S3 + CloudFront + ACM + Route 53, SSM, CodePipeline. Single `terraform apply`.
- **Branding:** App title = `coinBaby`, header = `coinBaby`, chat agent = `👶 Penny`.

### AWS services in use

| Area | Services |
|------|----------|
| **Backend** | VPC, RDS, EC2 + EIP, ECR, SSM, CloudWatch Logs, IAM |
| **Frontend** | S3, CloudFront, Route 53, ACM |
| **AI** | Bedrock (Claude 3.5 Haiku via inference profile) |
| **Auth** | Cognito User Pool + Pre Sign-Up Lambda |
| **CI/CD** | CodeCommit, CodeBuild, CodePipeline, S3 artifacts |

## Done (previously remaining)

- ~~Deploy Lambda + apply Terraform~~ ✓
- ~~Git cleanup (`__pycache__`)~~ ✓
- ~~Architecture diagram~~ ✓ (in README.md)
- ~~Custom domain~~ ✓ (`coinbaby.click` → CloudFront via Route 53 + ACM)

## Remaining steps

1. **Backend domain** — Point `api.coinbaby.click` to the backend EIP (Route 53 A record already supported in Terraform, just uncomment in tfvars). Update `VITE_API_URL` SSM param and re-run pipeline.
2. **Final E2E smoke test** — Fresh sign-up on `coinbaby.click`, full flow: wallets → transactions → budgets → goals → Penny chat.
3. **Project report / submission** — AWS Academy requirements checklist, architecture write-up, screenshots.
4. **Polish** — Error handling edge cases, loading states, mobile responsiveness if time permits.
