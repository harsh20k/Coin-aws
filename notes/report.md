# Project Report

## 1. Project Introduction

**coinBaby** is a smart personal finance advisor that brings all your financial accounts together, tracks every transaction, and provides tailored guidance through its AI assistant, Penny. More than just a ledger, coinBaby helps you set budgets, monitor goals, and get clear, practical advice for managing your money and making personal finance simple.

### Users

The typical user is an individual managing personal finances—not a business or accountant. They seek a clear, unified view of their accounts (e.g., cash, bank, savings) and straightforward feedback—all via an easy-to-use web app.

Accordingly, coinBaby targets a small to moderate user base (tens to low hundreds). It is not built for high-traffic; performance and capacity reflect its project-scale scope.

### Use-case

- **Auth** — Cognito sign-up and login should take under three seconds, with instant auto-confirmation (no email verification).
- **Transaction logging** — add, edit, or delete transactions instantly; recent transactions load within one second.
- **AI chat** — Penny's responses (DB query + Bedrock) should return in about five seconds.
- **Dashboard** — loads all key info in under two seconds.

### Infrastructure context

The app runs entirely on AWS. The backend is a FastAPI service running in a Docker container on a single EC2 instance. The database is a PostgreSQL RDS instance in a private subnet. The frontend is a React SPA deployed to S3 and served through CloudFront. Authentication is handled by Cognito.

This is a single-instance, single-region deployment — there is no auto-scaling, no multi-AZ failover. For a project of this scope and user base that is a deliberate and reasonable trade-off: it keeps the infrastructure simple, reproducible with a single `terraform apply`.

---

## 2. AWS Services — Selection and Justification

---

### Compute — EC2 + ECR + Lambda

- **EC2 (t3.micro)**
  - Runs python backend in Docker.
  - Free-tier eligible. Simple and direct: SSH in, see/manage everything.
  - Great for learning and transparency.
- **ECR**
  - Stores our Docker image.
- **Lambda**
  - Used only for Cognito post Sign-Up trigger(user get's automatically confirmed).
  - Good for short, event-driven tasks.

**Alternatives considered:**
- **ECS Fargate**
  - Overkill: Just for 1 container.
- **App Runner**
  - Too abstract. Less control, harder to learn from.
- **Lambda for backend**
  - Slow cold starts.
  - Problematic state: connection pools, schema setup don't work well as stateless functions.
- **Docker Hub**
  - Would require Docker credentials stored somewhere = more security risk.

---

### Storage — S3 + EBS

- **S3**
  - Hosts frontend static assets (React build).
  - Stores build artifacts from CI/CD (CodePipeline).
  - Cheap, durable, easy to manage.
- **EBS (gp3 SSD)**
  - 20 GB root disk for EC2.
  - Stores OS, Docker, logs. Fast and reliable.

**Alternatives considered:**
- **Amplify Hosting**
  - Easy but hides too much—want to see how S3, CloudFront, etc. fit together.
- **EFS**
  - Not needed—only 1 instance, no shared file storage.
- Using just EBS for everything? Not feasible for web static assets.

---

### Networking & Content Delivery — VPC + CloudFront + Route 53

- **VPC**
  - Custom subnets: public for EC2, private for RDS.
  - RDS only accessible from EC2, never public.
  - Security groups control access.
- **CloudFront**
  - Serves frontend (`coinbaby.click`), SPA routing, OAI — keeps S3 private.
  - Caches at edge locations.
- **Route 53**
  - Custom domain and DNS.
  - Alias records to CloudFront.
  - Handles ACM validation.

**Alternatives considered:**
- **Default VPC**
  - No subnet control. RDS could be public by mistake.
- **S3 website endpoint**
  - No HTTPS/custom domain support.
- **Skip custom domain**
  - `d1abc123.cloudfront.net` isn't user-friendly and it would be great to add a custom URL project on resume.
- **API Gateway**
  - Adds validation/rate limits, but backend already validates & authenticates.
  - Would just add extra cost and latency(extra hop) for this small scale.

---

### Database — RDS PostgreSQL

- **RDS PostgreSQL (db.t3.micro)**
  - Lives in private subnet, not public.
  - Handles all relational data: users, wallets, transactions, budgets/goals.
  - Automated backups, managed.
  - Clean separation between compute and data.

**Alternatives considered:**
- **DynamoDB**
  - Would need lots of data modeling and denormalization for relational needs. Not worth the extra effort here.
- **Aurora Serverless**
  - Scales to zero = cheap, but slow cold starts — bad for user experience in chat.
- **SQLite on EC2**
  - No backups, no recovery, not production. Would live on same disk as application.

---

## 3. Security — How Data Is Protected, Where It Isn't, and What Could Be Done

### What is actually protected

**Authentication — Cognito**

Users never authenticate directly against the backend. Cognito handles sign-up, login, and token issuance. On successful login, Cognito issues a JWT (JSON Web Token) — a signed, time-limited token the frontend attaches to every API request.

The backend validates that token on every protected route using a FastAPI dependency (`get_current_user`). It checks the signature against Cognito's public keys, verifies the expiry, and extracts the user identity. A request with a missing, expired, or tampered token is rejected with a 401 before any handler runs.

The algorithm is RS256 — asymmetric RSA signing. Cognito holds the private key and signs the token. The backend only needs the public key to verify it. There is no shared secret to leak.

**Database — private subnet + security groups**

RDS is not publicly accessible. `publicly_accessible = false` in Terraform, and the RDS security group only allows inbound connections on port 5432 from the backend security group — not from the internet, not from any other source. The only thing that can talk to the database is the EC2 instance running the backend.

**Database credentials — SSM Parameter Store**

The database password is generated at `terraform apply` time using `random_password` (24 characters, mixed special characters). It is never written to a `.env` file, never committed to git, never hardcoded anywhere.

It is stored in SSM Parameter Store as a `SecureString`. The EC2 instance reads it at startup via the AWS SDK, using its IAM role. No human ever needs to see or handle the password directly.

**EC2 disk — encrypted EBS**

The root EBS volume has `encrypted = true`. Data at rest on the instance — OS, Docker layers, logs — is encrypted.

**Frontend — OAI + CloudFront**

The S3 bucket holding the React build is fully private. No public access. The only entity allowed to read from it is the CloudFront Origin Access Identity (OAI) — a special IAM principal attached to the CloudFront distribution. Users can't hit the S3 URL directly. All traffic goes through CloudFront.

**IAM — least privilege per service**

Each AWS service gets its own IAM role with only the permissions it needs:

- **EC2 backend role** — `ssm:GetParameter` (to read config), `ecr:GetDownloadUrlForLayer` and related read-only ECR actions (to pull the Docker image), `bedrock:InvokeModel` (to call Penny's AI model), and `AmazonSSMManagedInstanceCore` (for SSM Run Command used by the deployment pipeline). Nothing else.
- **CodeBuild roles** — scoped to S3 artifact access, ECR push, SSM reads, and SSM Run Command on the EC2 instance.
- **Cognito Lambda trigger** — only allowed to call `cognito-idp:AdminConfirmSignUp` on the specific user pool.

No role has `AdministratorAccess`. No role has wildcard resource access beyond what was unavoidable during development.

---

### Where the data is vulnerable

**The backend is HTTP, not HTTPS.**

This is the most significant gap. API calls from the browser to the EC2 backend travel over plain HTTP. That means credentials (the JWT token in the `Authorization` header), financial transaction data, wallet names, budget figures — all of it is unencrypted in transit between the user's browser and the EC2 instance.

On a home network this is low risk. On public Wi-Fi it is a real exposure. A passive observer on the same network can read every request.

The fix is to put an ALB in front of EC2 with an ACM certificate, so the browser talks HTTPS to the ALB and the ALB forwards to EC2 over HTTP internally. The EC2 instance itself doesn't need a certificate. This adds ~$16/month for the ALB, which is why it was skipped for a project-scale deployment.

**SSH is open to a configured CIDR, not just localhost.**

The backend security group allows SSH (port 22) from `var.ssh_ingress_cidr`. In practice this is set to a specific IP, but it is still a surface. If that IP changes or the variable is set too broadly, SSH is exposed.

The better approach is to remove SSH entirely and use AWS Systems Manager Session Manager — which is already installed on the instance (`AmazonSSMManagedInstanceCore` is attached). Session Manager gives shell access through the AWS console or CLI, with no open port, no key pair, and a full audit trail in CloudTrail.

**The RDS subnet group uses public subnets.**

The `aws_db_subnet_group` uses `aws_subnet.public` — the same subnets as EC2. RDS is not publicly accessible (`publicly_accessible = false`), so this doesn't expose the database to the internet. But it is not ideal. The correct architecture is a dedicated private subnet with no route to the internet gateway, so even a misconfiguration can't accidentally expose RDS. For this project, the VPC only has public subnets — adding private subnets was skipped to keep the Terraform simpler.

**No WAF, no rate limiting.**

There is no Web Application Firewall in front of the backend. A determined attacker could send thousands of requests per second — either to exhaust the `t3.micro`'s CPU or to attempt brute-force attacks on the API. FastAPI has no built-in rate limiter. AWS WAF could be attached to CloudFront (for the frontend) or an ALB (for the backend) to block common attack patterns and enforce rate limits. For a project with a small, known user base this is an acceptable gap.

**No encryption at rest on RDS.**

The `aws_db_instance` resource does not set `storage_encrypted = true`. Financial data — transactions, wallets, budgets, goals — sits unencrypted on the RDS disk. AWS can add this with one line in Terraform, but it requires a snapshot-and-restore to apply to an existing instance.

---

### What further work would address these gaps

| Gap | Fix |
|---|---|
| HTTP backend | ALB + ACM cert, or Nginx + Let's Encrypt on EC2 |
| SSH exposure | Remove key pair, use SSM Session Manager exclusively |
| RDS in public subnet | Add private subnets, move RDS subnet group to private |
| No RDS encryption at rest | `storage_encrypted = true` in `rds.tf` |
| No rate limiting | AWS WAF on ALB, or `slowapi` middleware in FastAPI |

None of these are architecturally complex. They are deliberate trade-offs for a project-scale deployment — each one is a known gap, not an oversight.

---

### Security mechanisms — summary

| Mechanism | What it protects | Technology / service |
|---|---|---|
| JWT authentication | API access | Cognito, RS256-signed tokens |
| VPC + security groups | Database network isolation | AWS VPC, port-level rules |
| SSM SecureString | Database credentials at rest | AWS SSM Parameter Store + KMS (AES-256) |
| EBS encryption | EC2 disk data at rest | AWS KMS, AES-256 |
| S3 OAI | Frontend assets | CloudFront Origin Access Identity |
| ACM + CloudFront HTTPS | Frontend traffic in transit | TLS 1.2+, RSA/ECDSA cert |
| IAM least-privilege roles | Service-to-service access | AWS IAM, per-service roles |
| `publicly_accessible = false` | Database not reachable from internet | RDS config |
| Random 24-char DB password | Credential strength | Terraform `random_password` |

---

## 4. Cost Metrics — Up-Front, Ongoing, and Alternatives

Building and operating coinBaby in the real world requires understanding the full cost picture: one-time expenses, monthly recurring charges, and what we trade off by choosing this architecture over alternatives.

---

### Up-front / One-time costs

| Component                   | Cost              | Notes                                                          |
| --------------------------- | ----------------- | -------------------------------------------------------------- |
| **Domain (coinbaby.click)** | $3/yr (~$0.25/mo) | Purchased via Route 53                                         |
| **ACM SSL certificate**     | $0                | Free tier from AWS; auto-renewal                               |
| **AWS free tier**           | N/A               | Generous free tier covers most small deployments for 12 months |
**Total one-time (Year 1):** ~$13 + ~$13 for first 12 months of domain renewal = ~**$26** (or **~$2/mo amortized**).

After year one, the domain is the only ongoing up-front cost.

---

### Monthly operating costs (steady state, <100 users)

Assumptions:
- ~50–100 total users (low to moderate adoption)
- ~10–20 monthly active users
- ~5–10 AI chat requests per user per month (Bedrock calls)

| Service                             | Estimated cost | Breakdown                                                                                                                                                    |
| ----------------------------------- | -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **EC2 (t3.micro)**                  | $8–10/mo       | $0.0126/hr × 730 hrs/mo; free tier covers first 750 hrs (~31 days), so ~1 month is free, remainder paid. Real cost: ~$0–10/mo depending on free tier status. |
| **RDS (db.t3.micro)**               | $15–20/mo      | Similar free tier logic as EC2. Once free tier expires: ~$0.0166/hr × 730 = ~$12/mo + storage costs.                                                         |
| **RDS storage (20 GB)**             | ~$2–3/mo       | $0.115/GB/mo for gp2 (default); ~$2.30/mo.                                                                                                                   |
| **RDS backups (automated)**         | ~$0.50–1/mo    | First backup is free; additional snapshots billed at ~$0.10/GB/mo. With modest data, <$1.                                                                    |
| **S3 (frontend + artifacts)**       | <$1/mo         | Typical usage: <100 MB stored, <1M requests/mo = well under free tier (1 GB, 20k requests/mo free).                                                          |
| **CloudFront (frontend delivery)**  | ~$1–3/mo       | ~10k–50k monthly requests at ~$0.085/10k for US/EU egress. Negligible.                                                                                       |
| **Cognito**                         | <$1/mo         | Free tier: 50k monthly active users. Rarely hit limits.                                                                                                      |
| **Bedrock (Haiku 3.5)**             | ~$5–15/mo      | Input: $0.80/1M tokens; Output: $4.00/1M tokens. At ~1000 tokens/request, 50–150 requests/mo = ~$0.04–0.60/mo. Scales with usage.                            |
| **Lambda (Cognito trigger)**        | <$1/mo         | Free tier: 1M invocations/mo, 400k GB-seconds. Cognito trigger fires only on signup, rarely hits limits.                                                     |
| **ECR (image storage)**             | <$1/mo         | One Docker image ~500 MB. $0.10/GB/mo = ~$0.05/mo.                                                                                                           |
| **Systems Manager Session Manager** | $0             | Included with EC2 instance; no extra charge.                                                                                                                 |
| **CloudWatch logs**                 | ~$0.50–2/mo    | FastAPI / application logs; minimal volume on t3.micro. Mostly within free tier.                                                                             |
| **Route 53 (DNS)**                  | ~$0.250/mo     | $0.25/mo per hosted zone; 1 zone = $0.25/mo.                                                                                                                 |
| **VPC / Security Groups**           | $0             | No charge for VPC, subnets, or security groups themselves.                                                                                                   |

**Total steady-state monthly (after first 12 months):** ~**$35–60/mo**

**Breakdown:**
- Compute + storage (EC2 + RDS): ~$20–35/mo (biggest line item).
- Bedrock AI: ~$5–15/mo (variable with usage).
- Everything else: ~$5–10/mo (domain, CDN, databases, monitoring, DNS).

---

### Cost under growth / scaling scenarios

**100–500 users, moderate activity (20–50 MAU, 50–100 chat requests/day):**

| Change                                                          | Cost Impact                                 |
| --------------------------------------------------------------- | ------------------------------------------- |
| EC2 still t3.micro (handles ~50 concurrent)                     | +$0 (same instance)                         |
| RDS still db.t3.micro (handles ~100–200 concurrent connections) | +$0 (same instance)                         |
| Bedrock traffic 10x higher                                      | +$50–150/mo (scales linearly with requests) |
| CloudFront egress 5x higher                                     | +$1–2/mo (still negligible)                 |
| S3 storage grows to 500 MB                                      | +$0.20/mo                                   |

**Estimated cost at 300 users, moderate use:** ~**$90–120/mo**

**If you hit capacity (t3.micro maxed out):**

| Upgrade | Cost |
|---|---|
| Upgrade EC2 to t3.small (2x capacity) | +$20/mo |
| Upgrade RDS to db.t3.small | +$25/mo |
| Add ALB for HTTPS + rate limiting | +$16/mo |

**Total after scaling:** ~**$150–180/mo**

---

### Alternative architectures and cost comparison

#### Alternative 1: Serverless / API Gateway + Lambda + DynamoDB

**Architecture:**
- API Gateway (REST or HTTP)
- Lambda for all backend logic (no EC2)
- DynamoDB for user data
- S3 + CloudFront (unchanged)
- Cognito (unchanged)

**Cost estimate (same usage):**

| Service         | Cost                                                                                                                                          |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| API Gateway     | $3.50 per 1M requests; ~100k/mo = ~$0.35/mo                                                                                                   |
| Lambda          | Free tier: 1M invocations, 400k GB-seconds; ~500 invocations/mo × 1 sec each = well under free tier. **$0/mo**                                |
| DynamoDB        | On-demand: $1.25/M reads, $1.25/M writes. ~1000 reads/mo, ~500 writes/mo = ~$0.002/mo; or provisioned at $0.99/mo baseline = **~$0.99–1/mo**. |
| Bedrock         | Unchanged: **~$5–15/mo**                                                                                                                      |
| Everything else | ~$5/mo (same as before, minus RDS)                                                                                                            |


**Total serverless (steady state):** ~**$15–25/mo** ✅ 40–60% cheaper than EC2+RDS.

**Why it wasn't chosen:**
- Lambda cold starts (~2–5s) hurt the UX requirement of "AI chat response in ~5s".
- DynamoDB requires significant data modeling and denormalization for relational queries (budgets, goals, transactions with categories). Much more complex.
- Learning value: EC2 + RDS is more transparent and educational especially with separate course for serverless. 

---

#### Alternative 2: Amplify + DynamoDB

**Architecture:**
- AWS Amplify Hosting (automatic CI/CD, HTTPS, global CDN).
- Amplify GraphQL (AppSync) for backend.
- DynamoDB for data.
- Cognito (unchanged).

**Cost estimate:**
- Amplify Hosting: ~$1/mo (after 15 GB build storage free tier)
- AppSync (GraphQL): $1.25/1M reads + $1.25/1M writes; ~$5–10/mo at this scale.
- DynamoDB: ~$1/mo (on-demand) or ~$1/mo (provisioned).
- Bedrock: ~$5–15/mo (unchanged).
- S3 + everything else: ~$3–5/mo.

**Total Amplify + AppSync:** ~**$15–30/mo** ✅ Cheaper than EC2+RDS.

**Why it wasn't chosen:**
- Amplify abstracts away too much; it's harder to understand the underlying infrastructure.
- AppSync (GraphQL) is powerful but overkill for a simple transactional API.
- For a learning project, EC2+RDS is more hands-on.

---

### Justification: Why this architecture despite cost?

| Decision                             | Cost trade-off           | Justification                                                                                               |
| ------------------------------------ | ------------------------ | ----------------------------------------------------------------------------------------------------------- |
| EC2 + RDS over Lambda + DynamoDB     | +$30–40/mo               | Transparency. Easy SSH/debugging. Better UX (no cold starts). Easier relational queries. Educational value. |
| Custom backend over Amplify          | +$20–30/mo               | Full control. No vendor lock-in. Learn CloudFormation/Terraform. Understand infrastructure.                 |
| CloudFront + S3 over Amplify Hosting | Roughly equal (~$1–2/mo) | Same reasoning: control and learning.                                                                       |
| ALB not included (HTTP backend)      | -$16/mo                  | Deliberate trade-off. Adds cost for a 12-person project. Security acceptable for this scope.                |


---

### Summary

| Timeframe | Cost | Notes |
|---|---|---|
| **Year 1 (with free tier)** | ~$200–300 total (~$16–25/mo average) | Free tier covers most of the year. |
| **Steady state (after free tier expires)** | ~$35–60/mo | Sustainable for 50–100 users, moderate activity. |
| **Scaled (300 users, high activity)** | ~$90–120/mo | Before needing to upgrade instances. |
| **Production-grade (scaled + HA)** | ~$150–250/mo | Add ALB, multi-AZ RDS, WAF, etc. |

**Bottom line:** This architecture is cost-efficient for a project serving tens to a few hundred users. The monthly cost (~$40–60) is sustainable for a personal project. Serverless would save ~40%, but adds complexity not justified at this scale. The current setup prioritizes **learning, transparency, and reasonable UX** over squeezing the last dollar of marginal cost savings.

---

## 5. Future — Evolution and Next Features

If coinBaby were to continue development, the roadmap would evolve across three timelines: near-term (3–6 months), medium-term (6–12 months), and long-term (12+ months). Each phase adds capabilities while respecting the current architecture's simplicity and cost-efficiency.

---

### Near-term features (3–6 months)

**1. Conversation memory and function calling**
- Store chat history in RDS (`chat_messages` table) so Penny remembers context.
- Use Bedrock's function-calling API for tools like `get_transactions_for_category(category, date_range)` instead of sending all data upfront.
- **Services:** RDS only. **Cost:** +$0–1/mo.

**2. Mobile app (iOS/Android)**
- React Native or Flutter frontend; same FastAPI backend.
- Offline-first with local SQLite; sync when online.
- Push notifications via SNS for budget alerts and goals.
- **Services:** Amplify Gen2, SNS, CodeBuild. **Cost:** +$5–10/mo.

**3. Natural language transaction input and auto-categorization**
- Users type or speak transactions naturally ("Spent $45 on groceries at Superstore").
- Use Bedrock to parse intent, extract amount, category, merchant, and date.
- Auto-categorize based on merchant name or historical patterns; suggest corrections if ambiguous.
- **Services:** Bedrock, Lambda (optional for batch categorization) (scales with transaction volume).

---

### Medium-term features (6–12 months)

**4. Advanced analytics and exports**
- Spending trends, category breakdowns, tax summaries.
- QuickSight or self-hosted Metabase for dashboards; Lambda for PDF generation and email delivery.
- **Services:** QuickSight, Lambda, SES, S3..

**5. Multi-user / household budgets**
- Families/roommates share budgets and view each other's transactions.
- New RDS schema: `household`, `household_members`, `user_roles`. Cognito for household attributes.
- **Services:** RDS (consider read replica for analytics).

---

### Long-term features (12+ months)

**6. Machine learning (categorization and anomaly detection)**
- Auto-categorize transactions; alert on unusual spending (e.g., $5k grocery bill when average is $100).
- Train classification model via SageMaker; deploy as real-time endpoint or batch job.
- **Services:** SageMaker, S3, Lambda.

**7. Proactive financial advice**
- Penny suggests actions ("You're on pace to overspend on dining. Cut back to stay within budget.").
- Build knowledge graph of spending patterns; cache in ElastiCache (Redis). Use Bedrock Claude Opus instead of Haiku.
- Trigger on dashboard load or daily digest via SES.
- **Services:** Bedrock Opus, ElastiCache (Redis), SES.

**8. Multi-region HA deployment**
- Replicate to second region for reliability or global user base.
- Aurora Global Database (multi-region read replica); EC2 in both regions behind ALB; Route 53 failover; S3 CRR.
- **Services:** Aurora Global, ALB (2 regions), Route 53, EC2 (second region).

---

### Phased roadmap

| Phase | Focus | Cost | Justification |
|---|---|---|---|
| **Phase 1 (Now)** | Conversation memory + function calling | +$0–1/mo | Quick win; no new services |
| **Phase 2 (3–6 mo)** | Bank sync (Plaid) | +$100–500/mo | Main value unlock; users pay for auto-import |
| **Phase 3 (6–12 mo)** | Mobile + analytics | +$30–60/mo | Retention and stickiness |
| **Phase 4 (12+ mo)** | ML + proactive advice | +$50–200/mo | Differentiation; justify premium tier |
| **Phase 5 (scale)** | Multi-region HA | +$100–150/mo | Only if user base >500 or compliance mandated |

---

### Cloud service evolution

| Current | Phase 2 | Phase 3 | Phase 4 | Phase 5 |
|---|---|---|---|---|
| EC2 (t3.micro) | EC2 (t3.micro) | EC2 (t3.small) | ECS/Fargate | ECS + multi-region |
| RDS PostgreSQL | RDS PostgreSQL | RDS + read replica | Aurora | Aurora Global |
| Bedrock Haiku | Bedrock Haiku | Bedrock Haiku | Bedrock Opus | Bedrock Opus |
| Lambda (Cognito) | Lambda (Plaid) | Lambda (PDF) | Lambda (SageMaker) | Lambda (multi-region) |
| — | Plaid + EventBridge | Plaid + QuickSight + SNS | Plaid + SageMaker + ElastiCache | Same + SES |

Each phase is additive, non-breaking, and prioritized by user feedback.



