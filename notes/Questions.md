# Instructor Questions and Answers

## Question 1: Private vs Public Subnets and RDS Placement

**Question:**
You mentioned that RDS is placed in a "private subnet" but then later stated that "the RDS subnet group uses public subnets" and that `publicly_accessible = false` prevents it from being exposed. Can you explain the difference between a subnet being "private" versus "public" in AWS VPC terms, and clarify whether your RDS is actually in a private subnet or a public subnet? What makes a subnet private?

**Answer:**
A subnet is considered **public** if its route table has a route to an Internet Gateway (IGW), allowing direct internet communication. A subnet is **private** if it does NOT have a route to an IGW.

In my project, the RDS is actually in a **public subnet** (with IGW route), but I've set `publicly_accessible = false` and restricted the security group to only allow connections from the EC2 security group. This makes it functionally protected but architecturally suboptimal.

The correct architecture would have dedicated private subnets (no IGW route) for RDS, providing defense in depth—even if someone accidentally sets `publicly_accessible = true`, the database still couldn't be reached from the internet because the subnet itself has no internet route.

---

## Question 2: JWT Token Validation

**Question:**
You mentioned the backend validates JWT tokens using RS256 asymmetric signing. Walk me through what happens when a request arrives at your backend with an Authorization header. How does the backend verify the token is legitimate? What specific checks are performed?

**Expected Answer:**
- Extract the JWT from the Authorization header
- Fetch Cognito's public keys (JWKS endpoint) or use cached keys
- Verify the token signature using RS256 and Cognito's public key
- Check token expiration (`exp` claim)
- Verify the issuer (`iss` claim matches the Cognito user pool)
- Verify the audience (`aud` or `client_id` matches the app client)
- Extract the `sub` (subject) claim to identify the user
- Reject with 401 if any check fails

---

## Question 3: HTTP vs HTTPS Trade-off

**Question:**
You identified that the backend uses HTTP instead of HTTPS as the most significant security gap. You suggested adding an ALB with ACM certificate would fix this for ~$16/month. Why specifically does this fix the problem? What does the traffic flow look like before and after adding the ALB?

**Expected Answer:**

**Current flow (vulnerable):**
Browser → (HTTPS) → CloudFront → S3 (frontend)
Browser → (HTTP) → EC2 (backend) ← JWT tokens and financial data in plaintext

**With ALB (secure):**
Browser → (HTTPS) → CloudFront → S3 (frontend)
Browser → (HTTPS) → ALB → (HTTP) → EC2 (backend)

The ALB terminates TLS/SSL using an ACM certificate, so traffic between the browser and ALB is encrypted. The ALB to EC2 traffic is still HTTP, but that's internal to the VPC and not exposed to public networks, making it acceptable.

---

## Question 4: Database Credential Management

**Question:**
You store the database password in SSM Parameter Store as a SecureString. How does the EC2 instance authenticate to SSM to retrieve this credential? What prevents an attacker who gains access to the EC2 instance from reading it?

**Expected Answer:**
The EC2 instance has an IAM role attached with `ssm:GetParameter` permission for the specific parameter. The instance uses the AWS SDK to retrieve the credential using temporary credentials from the instance metadata service (IMDS).

If an attacker gains access to the EC2 instance (SSH or code execution), they CAN read the credential because the IAM role grants that permission. SSM Parameter Store protects against:
- Credentials being exposed in code/git
- Credentials being visible in the AWS console
- Accidental logging of credentials
- Encryption at rest (using KMS)

It does NOT protect against a compromised instance. For that, you'd need additional controls like secrets rotation, monitoring, or using a service like Secrets Manager with automatic rotation.

---

## Question 5: Cost Comparison - Why Not Serverless?

**Question:**
Your cost analysis shows that a serverless architecture (Lambda + DynamoDB) would be 40-60% cheaper (~$15-25/mo vs ~$35-60/mo). You cited Lambda cold starts, DynamoDB complexity, and learning value as reasons not to choose it. For a real business with 100 users, would you still make the same decision? Justify your reasoning from a business perspective, not just a learning perspective.

**Expected Answer:**
For a real business with 100 paying users, the decision depends on priorities:

**Arguments FOR staying with EC2+RDS:**
- Better user experience (no cold starts, <5s AI responses)
- PostgreSQL allows complex relational queries without denormalization
- Easier to debug and monitor (SSH access, familiar SQL)
- Predictable costs (fixed ~$40-60/mo regardless of usage spikes)

**Arguments FOR switching to serverless:**
- ~$20-40/mo cost savings = $240-480/year
- True auto-scaling (handles traffic spikes without manual intervention)
- Pay only for what you use (if users are inactive, costs drop)
- No server maintenance or patching

For 100 users, I'd likely **stay with EC2+RDS** because:
- The ~$30/mo difference is minimal compared to user experience impact
- Cold starts would hurt the AI chat feature (core value proposition)
- With 100 users, you can justify fixed infrastructure costs
- If cost becomes critical, optimizing Bedrock usage would save more than switching to serverless

At 1000+ users, serverless becomes more attractive due to auto-scaling benefits.

---

## Question 6: CloudFront OAI (Origin Access Identity)

**Question:**
You mentioned CloudFront uses an OAI to access the S3 bucket. What problem does this solve? What would happen if you just made the S3 bucket public and pointed CloudFront to it?

**Expected Answer:**
The OAI ensures that users can ONLY access the frontend through CloudFront, not directly via the S3 URL.

**Without OAI (public bucket):**
- Users could bypass CloudFront by accessing `https://coinbaby-frontend.s3.amazonaws.com/index.html`
- You'd pay for S3 data transfer costs instead of CloudFront's cheaper rates
- You'd lose CloudFront's edge caching benefits (higher latency)
- You couldn't enforce HTTPS or custom domain on the S3 endpoint
- Harder to implement security headers, WAF, or rate limiting

**With OAI:**
- S3 bucket policy ONLY allows access from the CloudFront OAI
- Users must go through CloudFront (custom domain, HTTPS, caching)
- Direct S3 access returns 403 Forbidden
- Better security and cost control

---

## Question 7: Cognito Lambda Trigger - Auto-Confirmation

**Question:**
You use a Lambda function triggered by Cognito post-signup to auto-confirm users. Why not just enable auto-confirmation directly in Cognito settings? What does the Lambda actually do, and when would you NOT want auto-confirmation?

**Expected Answer:**
Cognito doesn't have a built-in "auto-confirm without verification" setting. By default, Cognito requires email or phone verification before confirming a user.

The Lambda trigger receives the `PostConfirmation_ConfirmSignUp` event and calls `AdminConfirmSignUp` to immediately activate the account without waiting for email verification.

**Why I used this:**
- Faster onboarding (no email verification step)
- Simpler UX for a project/demo environment
- No email delivery delays

**When you would NOT want auto-confirmation:**
- Production apps requiring verified email addresses (password resets, notifications)
- Preventing bot signups (email verification acts as CAPTCHA)
- Regulatory requirements (proving user owns the email)
- Preventing typos in email addresses

For a real production app, I would remove the Lambda trigger and use Cognito's standard email verification flow.

---

## Question 8: EC2 Instance Sizing

**Question:**
You chose a t3.micro instance. What are the specs of a t3.micro (vCPUs, RAM)? How many concurrent users can it realistically handle? What would be the first bottleneck: CPU, memory, network, or database connections?

**Expected Answer:**
**t3.micro specs:**
- 2 vCPUs (burstable)
- 1 GB RAM
- Up to 2085 Mbps network bandwidth
- Baseline CPU performance: 10% (with burst credits)

**Concurrent users:** ~20-50 concurrent active users, depending on workload
**Total users:** ~100-200 total users with moderate activity

**First bottleneck:** Likely **memory (RAM)**
- FastAPI application + connection pool + Docker overhead = ~300-500 MB
- Each concurrent request = ~10-50 MB
- AI chat requests (Bedrock calls) = ~100-200 MB during processing
- At ~1 GB total, you can handle ~5-10 concurrent AI chat requests

**Second bottleneck:** **CPU** (if Bedrock calls are CPU-heavy for JSON parsing)

**Database connections** would be third—RDS t3.micro can handle 100+ concurrent connections, but your app likely pools 10-20 max.

**Upgrade path:** t3.small (2 GB RAM, 20% baseline CPU) would double capacity for +$15-20/mo.

---

## Question 9: Bedrock Model Selection

**Question:**
You use Claude Haiku 3.5 for the AI assistant. Why Haiku instead of Sonnet or Opus? What are the trade-offs? How would the cost and user experience change if you switched to Sonnet?

**Expected Answer:**
**Haiku vs Sonnet vs Opus:**

| Model | Speed | Intelligence | Cost (input/output per 1M tokens) |
|-------|-------|--------------|-----------------------------------|
| Haiku | Fastest | Good | $0.80 / $4.00 |
| Sonnet | Fast | Better | $3.00 / $15.00 |
| Opus | Slowest | Best | $15.00 / $75.00 |

**Why Haiku:**
- Fast responses (~1-2s), meeting the 5s total requirement
- Good enough for basic financial queries ("How much did I spend on groceries?")
- Cheapest option (~$5-15/mo for 50-150 requests)

**If I switched to Sonnet:**
- **Cost:** ~4x higher (~$20-60/mo instead of $5-15/mo)
- **Speed:** Slightly slower (~2-3s instead of ~1-2s)
- **Quality:** Better reasoning, more nuanced financial advice
- **UX impact:** Minimal—Haiku is already good enough for this use case

**When to use Sonnet:**
- Complex financial planning (multi-step reasoning)
- Proactive advice generation (Phase 4 in roadmap)
- Users paying for premium tier

For the current MVP with simple queries, Haiku is the right choice.

---

## Question 10: Terraform State Management

**Question:**
Your report mentions deploying infrastructure with `terraform apply`. Where is your Terraform state file stored? What are the risks of local state, and how would you improve this for a team environment?

**Expected Answer:**
**Likely current setup:** Local state file (`terraform.tfstate`) stored in the project directory.

**Risks of local state:**
- Single point of failure (if lost, infrastructure is unmanageable)
- No collaboration (two people running `terraform apply` simultaneously = state corruption)
- No versioning/history (can't rollback or audit changes)
- Secrets stored in plaintext in state file (database password, etc.)
- No locking (concurrent applies can corrupt state)

**Improvement for team environment:**
Use **remote state backend** with S3 + DynamoDB:

```hcl
terraform {
  backend "s3" {
    bucket         = "coinbaby-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}
```

**Benefits:**
- Centralized state in S3 (versioned, encrypted)
- State locking via DynamoDB (prevents concurrent applies)
- Team collaboration (everyone uses same state)
- Backup and disaster recovery (S3 versioning)

**Cost:** ~$1-2/mo (S3 storage + DynamoDB on-demand)

---

## Question 11: CI/CD Pipeline with CodePipeline

**Question:**
Your report mentions CodePipeline and CodeBuild for CI/CD. Walk me through what happens when you push code to the main branch. What stages does the pipeline have, and how does the backend get updated on EC2?

**Expected Answer:**
**Pipeline flow:**

1. **Source stage:** Detects push to GitHub main branch
2. **Build stage (CodeBuild):**
   - Pulls source code
   - Runs tests (if any)
   - Builds Docker image
   - Pushes image to ECR with new tag
   - Stores build artifacts in S3
3. **Deploy stage (CodeBuild + SSM):**
   - Uses SSM Run Command to execute commands on EC2:
     - Pull new Docker image from ECR
     - Stop old container
     - Start new container with updated image
   - Or manually SSH and run `docker pull` + `docker restart`

**For frontend:**
- CodeBuild runs `npm run build`
- Syncs build files to S3 bucket
- Invalidates CloudFront cache (`aws cloudfront create-invalidation`)

**Key IAM permissions needed:**
- CodeBuild role: ECR push, S3 write, SSM SendCommand
- EC2 role: ECR pull, SSM managed instance core

**Improvement:** Use blue-green deployment or health checks to avoid downtime during deployment.

---

## Question 12: Database Backups and Disaster Recovery

**Question:**
You mentioned RDS has automated backups. What is the retention period? If the database is corrupted or accidentally deleted, what is your recovery process? How much data would you lose?

**Expected Answer:**
**RDS automated backups (default):**
- Retention: 7 days (configurable 1-35 days)
- Daily snapshots + transaction logs (point-in-time recovery)
- Stored in S3 (managed by AWS)

**Recovery process:**
1. Go to RDS console or use AWS CLI
2. Restore from automated backup or manual snapshot
3. Creates a NEW RDS instance (can't restore in-place)
4. Update backend connection string to point to new instance
5. Redeploy backend with new endpoint

**Data loss:** 
- With point-in-time recovery: lose up to 5 minutes of data
- With snapshot: lose data since last snapshot (up to 24 hours)

**Current gaps:**
- No testing of restore process (do backups actually work?)
- Manual DNS/connection string update required
- Downtime during restore (~10-30 minutes)

**Improvements:**
- Increase retention to 14-30 days
- Regular restore testing (quarterly)
- Multi-AZ deployment for automatic failover (eliminates downtime)
- Use Aurora with continuous backups (1-second point-in-time recovery)

---

## Question 13: Security Groups vs NACLs

**Question:**
You mentioned using security groups to control access between EC2 and RDS. What is the difference between security groups and Network ACLs (NACLs) in AWS? When would you use one versus the other?

**Expected Answer:**
**Security Groups:**
- **Stateful:** Return traffic automatically allowed
- **Instance-level:** Attached to ENIs (network interfaces)
- **Allow rules only:** Can't explicitly deny
- **Evaluated together:** All rules evaluated; most permissive wins
- **Default:** Deny all inbound, allow all outbound

**NACLs:**
- **Stateless:** Must explicitly allow both inbound and outbound
- **Subnet-level:** Applied to all resources in a subnet
- **Allow and deny rules:** Can explicitly block traffic
- **Rule order matters:** Processed in numerical order (lowest first)
- **Default:** Allow all inbound and outbound

**When to use Security Groups (most common):**
- Application-level control (e.g., "only backend can access RDS")
- Easier to manage (stateful = simpler rules)
- Dynamic references (can reference other security groups)

**When to use NACLs:**
- Subnet-level blocking (e.g., block specific IP ranges across all resources)
- Defense in depth (second layer after security groups)
- Explicit deny rules (e.g., block known malicious IPs)

**For coinBaby:**
- Security groups are sufficient (EC2 → RDS, ALB → EC2)
- NACLs would add complexity without much benefit at this scale

---

## Question 14: Connection Pooling

**Question:**
You mentioned the backend uses connection pooling. Why is this important for a database-backed application? What happens without connection pooling? What library does FastAPI/SQLAlchemy use for this?

**Expected Answer:**
**Why connection pooling matters:**
- Opening a new database connection is expensive (TCP handshake, authentication, session setup = 50-200ms)
- Without pooling, every API request opens and closes a connection
- With 10 concurrent requests, you'd open 10 new connections = high latency + CPU overhead

**Connection pool:**
- Pre-establishes N connections at startup (e.g., 5-10)
- Reuses connections across requests
- Queues requests if all connections are busy

**In Python/FastAPI:**
- **SQLAlchemy** manages the pool (`create_engine` with `pool_size` and `max_overflow`)
- Typical config: `pool_size=5, max_overflow=10` (5 persistent, up to 15 total)

**Without pooling:**
- Slow API responses (every request adds 50-200ms)
- Database connection limit exhausted (RDS t3.micro max ~100 connections)
- Higher database CPU usage

**Trade-off:**
- Too small pool = requests wait in queue
- Too large pool = idle connections waste memory on RDS

**For t3.micro backend + db.t3.micro RDS:** pool_size=5-10 is reasonable.

---

## Question 15: Rate Limiting and DDoS Protection

**Question:**
You identified lack of rate limiting as a security gap. If an attacker sends 10,000 requests per second to your backend, what happens? Where in your architecture could you add rate limiting, and what AWS service would you use?

**Expected Answer:**
**What happens now (no rate limiting):**
- EC2 t3.micro gets overwhelmed (CPU maxed out)
- Application becomes unresponsive
- Legitimate users can't access the service
- Potential crash or instance freeze
- CloudWatch shows high CPU/network metrics

**Where to add rate limiting:**

**Option 1: AWS WAF on ALB (best)**
- Attach WAF Web ACL to ALB
- Rate-based rule: "Block IPs exceeding 100 requests per 5 minutes"
- Cost: ~$5-10/mo (WAF + rule charges)

**Option 2: AWS WAF on CloudFront**
- Only protects frontend (S3)
- Doesn't protect backend API directly unless backend is also behind CloudFront

**Option 3: Application-level (FastAPI middleware)**
- Use `slowapi` library (Flask-Limiter equivalent)
- Example: `@limiter.limit("10 per minute")`
- Downside: Attacker's requests still reach EC2 (wastes compute)

**Option 4: Cognito-level**
- Limit authenticated users only
- Doesn't protect unauthenticated endpoints (e.g., `/health`)

**Best approach:**
- WAF on ALB with rate-based rules (blocks before reaching EC2)
- Application-level as secondary defense (per-user limits)

**Additional protection:**
- CloudFront has built-in DDoS protection (AWS Shield Standard)
- Upgrade to Shield Advanced for advanced DDoS protection (~$3000/mo—not justified for this scale)

