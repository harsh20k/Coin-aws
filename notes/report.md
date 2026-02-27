# Project Report

## 1. Project Introduction

**coinBaby** is a smart personal finance advisor that brings all your financial accounts together, tracks every transaction, and provides tailored guidance through its AI assistant, Penny. More than just a ledger, coinBaby helps you set budgets, monitor goals, and get clear, practical advice for managing your money and making personal finance simple.

### Users

The typical user is an individual managing personal finances—not a business or accountant. They seek a clear, unified view of their accounts (e.g., cash, bank, savings) and straightforward feedback—all via an easy-to-use web app.

Accordingly, coinBaby targets a small to moderate user base (tens to low hundreds). It is not built for high-traffic; performance and capacity reflect its project-scale scope.

### Use-case

- **Auth** — Cognito sign-up and login should take under three seconds, with instant auto-confirmation (no email verification).
- **Transaction logging** — add, edit, or delete transactions instantly; recent transactions load within one second.
- **AI chat** — Penny’s responses (DB query + Bedrock) should return in about five seconds.
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
  - Problematic state: connection pools, schema setup don’t work well as stateless functions.
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
  - `d1abc123.cloudfront.net` isn’t user-friendly and it would be great to add a custom URL project on resume.
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

Security in coinBaby isn't a single feature — it's a set of choices made at each layer of the stack. Some of those choices are solid. Some are deliberate compromises for a project of this scope. And a few are genuine gaps that would need addressing before this ran in production.

Let's go through each layer honestly.

---

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

