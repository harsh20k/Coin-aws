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

