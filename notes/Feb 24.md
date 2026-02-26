## EC2 Disk Space Issue (Feb 24)

**Problem:** Backend deployment failing with `failed to register layer: write /usr/local/lib/python3.12/site-packages/sqlalchemy/sql/__pycache__/selectable.cpython-312.pyc: no space left on device` during Docker image pull.

**Root Cause:** 
- EC2 t3.micro instance with default 8GB EBS volume
- Docker consuming 5.3GB of 6.1GB total space in `/var`
- Old Docker images, containers, layers, and volumes accumulating over time
- No cleanup happening between deployments

**Solution:**

1. **Immediate Fix (buildspec-backend-deploy.yml):**
   - Added `sudo docker system prune -af --filter "until=24h"` before Docker pull
   - Initially tried `--volumes` flag but got error: "The 'until' filter is not supported with '--volumes'"
   - Final command: `sudo docker system prune -af --filter "until=24h"`
   - Removes all stopped containers, unused images, and build cache older than 24 hours
   - Runs automatically on each deployment to free up space

2. **Long-term Fix (ec2.tf):**
   - Added `root_block_device` configuration to increase EBS volume from 8GB to 20GB
   - Set volume type to `gp3` with encryption enabled
   - Requires `terraform apply` to create new instance with larger disk

**Files Changed:**
- `buildspec-backend-deploy.yml` - Added Docker cleanup step (removed `--volumes` flag for compatibility)
- `infra/terraform/ec2.tf` - Increased EBS volume size

---

## Chat Feature Failure - Claude Model Upgrade (Feb 24)

**Problem:** Chat endpoint returning "load failed" error. Backend logs showed various Bedrock API errors.

**Debug Journey:**

### Issue 1: Debug Instrumentation Failure
- Added Python logging that tried to write to local filesystem path
- **Error**: `FileNotFoundError: /Users/harsh/Artifacts/Dalla/.cursor/debug-13f9d1.log`
- **Fix**: Removed file-based debug logging, switched to Python's standard `logging` module

### Issue 2: Claude 4.5 Haiku ValidationException
- Attempted upgrade from Claude 3 Haiku to Claude 4.5 Haiku
- Model ID: `anthropic.claude-haiku-4-5-20251001-v1:0`
- **Error**: `ValidationException` - Model not available or enabled in region
- **Root Cause**: Claude 4.5 Haiku not yet available or requires model access enablement in Bedrock console

### Issue 3: Claude 3.5 Haiku On-Demand Throughput Error
- Switched to Claude 3.5 Haiku: `anthropic.claude-3-5-haiku-20241022-v1:0`
- **Error**: "Invocation of model ID with on-demand throughput isn't supported. Retry your request with the ID or ARN of an inference profile"
- **Root Cause**: Newer Claude models (3.5+) require using inference profiles instead of direct model IDs for on-demand throughput
- **Fix**: Changed to inference profile ID: `us.anthropic.claude-3-5-haiku-20241022-v1:0`

### Issue 4: IAM Permission - Wrong ARN Format
- Updated IAM policy but still got `AccessDeniedException`
- **Error**: Tried to use `arn:aws:bedrock:region::foundation-model/inference-profile-id`
- **Root Cause**: Inference profiles use different ARN format than foundation models
- **Fix**: Updated IAM policy to include both:
  - `arn:aws:bedrock:*::foundation-model/*`
  - `arn:aws:bedrock:*:*:inference-profile/*`

### Issue 5: Cross-Region Routing Denial
- Still getting `AccessDeniedException` after IAM update
- **Error**: "User is not authorized to perform: bedrock:InvokeModel on resource: arn:aws:bedrock:us-east-2::foundation-model/anthropic.claude-3-5-haiku..."
- **Root Cause**: Inference profile `us.anthropic.claude-3-5-haiku-20241022-v1:0` routes requests to **us-east-2** for load balancing, but IAM policy only allowed `us-east-1` foundation models
- **Key Insight**: Inference profiles use cross-region routing, so permissions must allow foundation models from **all regions**, not just the primary region
- **Final Fix**: Changed IAM policy from `arn:aws:bedrock:${var.aws_region}::foundation-model/*` to `arn:aws:bedrock:*::foundation-model/*` (wildcard region)

**Final Solution:**

1. **Backend Code (chat.py):**
   - Model ID: `us.anthropic.claude-3-5-haiku-20241022-v1:0` (inference profile)
   - Added proper logging with Python's `logging` module
   - Removed broken file-based debug instrumentation

2. **IAM Policy (ec2.tf):**
   ```hcl
   resources = [
     "arn:aws:bedrock:*::foundation-model/*",
     "arn:aws:bedrock:*:*:inference-profile/*"
   ]
   ```
   - Wildcard region (`*`) to support cross-region inference profile routing
   - Both foundation models and inference profiles allowed

**Key Learnings:**
- Claude 3.5+ models require inference profiles, not direct model IDs
- Inference profiles use cross-region routing for load balancing and availability
- IAM policies must allow foundation models from all regions when using inference profiles
- Always check actual error messages in logs - they reveal the exact resource being accessed

**Files Changed:**
- `backend/app/routers/chat.py` - Updated to use inference profile ID, added logging
- `infra/terraform/ec2.tf` - Updated IAM policy with wildcard region and inference profile ARNs

**Testing:**
- Ran `terraform apply` to update IAM permissions
- Chat feature now working with Claude 3.5 Haiku via inference profile
- ✅ Confirmed working on Feb 24, 2026

---

## coinBaby Persona + Dashboard Redesign (Feb 24)

### coinBaby Prompt (`backend/app/routers/chat.py`)
- Replaced generic "helpful financial assistant" prompt with **coinBaby** persona
- coinBaby = playful toddler who loves coins, gives positive reinforcement for saving/investing
- Empathizes that spending on things you love is also OK
- Rules: short sentences, 3–5 sentence max, no markdown headers, no asking for info unless critical
- Used Claude's `system` field for the persona (separate from financial data in `user` turn)
- Reduced `max_tokens` to 350 to enforce conciseness
- Backend now returns `[SYSTEM] ... [USER] ...` block as the `prompt` field in response (for debugging/display)

### Dashboard Redesign (`frontend/src/pages/Dashboard.tsx` + `Dashboard.css`)
Replaced simple nav-card grid with a full **3-column layout**:

**Left sidebar — Wallets, Goals, Budgets**
- Wallets: name + computed balance (green if positive, red if negative) derived from transactions
- Goals: progress bars (blue fill), `current / target` computed from matching transactions in period
- Budgets: progress bars (green fill, turns red if over limit), spend computed from transactions

**Center — coinBaby Chat**
- Inline chat widget (no need to navigate to `/chat`)
- Full message history with user bubbles (blue, right-aligned) and AI bubbles (grey, left-aligned)
- Each AI reply has a collapsible **"Prompt sent to Claude"** section showing the full raw prompt

**Right sidebar — Recent Transactions**
- Last 10 transactions sorted by date desc
- Green `+` for income, red `−` for all outflows
- Shows: sign, amount, subcategory name, date

### Other
- `frontend/src/api/types.ts` — added `prompt?: string` to `ChatResponse`
- `frontend/src/components/Layout.css` — bumped `max-width` from `900px` to `1300px` for 3-column layout

---

## Cognito Auto-Confirm on Sign Up (Feb 24)

**Goal:** Allow users to sign up and immediately log in without email verification.

**Problem:** Cognito's default sign-up flow puts users in `UNCONFIRMED` state until they verify their email. There's no native setting to skip this.

**Solution:** Pre Sign-Up Lambda trigger that auto-confirms users.

**How it works:**
- `infra/terraform/lambda/index.py` — 4-line Lambda that sets `autoConfirmUser = True` and `autoVerifyEmail = True` in the Cognito Pre Sign-Up event response
- `autoConfirmUser` is the critical flag — skips `UNCONFIRMED` state so user can log in immediately
- `autoVerifyEmail` marks email as verified in user attributes

**Terraform changes (`infra/terraform/main.tf`):**
- `aws_iam_role.auto_confirm_lambda` — execution role for the Lambda
- `aws_iam_role_policy_attachment` — attaches `AWSLambdaBasicExecutionRole`
- `aws_lambda_function.auto_confirm` — deploys `lambda/auto_confirm.zip`
- `aws_cognito_user_pool.main` — added `lambda_config { pre_sign_up = ... }`
- `aws_lambda_permission.cognito_pre_signup` — allows Cognito to invoke the Lambda

**IAM issue during deployment:**
- `dalla-project-owner` IAM user lacked `lambda:CreateFunction` and `lambda:ListVersionsByFunction` permissions
- Fixed by adding inline policy with `lambda:*` scoped to `arn:aws:lambda:us-east-1:411960113601:function:dalla-*`

---

## UI Renames (Feb 24)

- `frontend/index.html` — page title changed from `Dalla` to `coinBaby`
- `frontend/src/components/Layout.tsx` — app header changed from `theCoin` to `coinBaby`
- `frontend/src/pages/Dashboard.tsx` — chat panel header changed from `🪙 coinBaby` to `👶 Penny`; hint + placeholder updated to match

---

## Quick Question Templates in Chat (Feb 24)

Added clickable quick-question chips to the Penny chat panel that appear when chat history is empty.

**Questions:**
- "Hey Penny, what is my major expense?"
- "Penny, how should I save more money toward my goals?"
- "Penny, where am I overspending this month?"
- "Hey Penny, give me a summary of my finances"

**Implementation:**
- Pill-shaped buttons rendered inside `db-chat-messages` when `chatHistory.length === 0`
- On click: sets message state and programmatically submits the chat form via `requestSubmit()`
- Chips disappear once conversation starts

**Files Changed:**
- `frontend/src/pages/Dashboard.tsx` — added quick question buttons in empty chat state
- `frontend/src/pages/Dashboard.css` — added `.db-chat-empty`, `.db-quick-questions`, `.db-quick-q` styles

---

## Git Cleanup (Feb 24)

- `__pycache__/` was being tracked despite being in `.gitignore` (committed before rule existed)
- Fix: `git rm -r --cached backend/app/__pycache__ backend/app/routers/__pycache__`

---

## Custom Domain Setup — coinbaby.click (Feb 24)

**Goal:** Point the Route 53 domain `coinbaby.click` at the CloudFront frontend so users access the app via `http://coinbaby.click` instead of the raw CloudFront URL.

**Why ACM is needed:** CloudFront requires an ACM certificate for any custom domain alias, even when `viewer_protocol_policy = "allow-all"` (HTTP still works). Since the stack is already in `us-east-1`, the cert is in the right region for CloudFront.

**Terraform changes (`infra/terraform/frontend.tf`):**

1. `aws_acm_certificate.frontend` — requests a cert for `coinbaby.click` with DNS validation
2. `aws_route53_record.frontend_cert_validation` — CNAME for DNS validation (automatic via Route 53)
3. `aws_acm_certificate_validation.frontend` — waits until cert is issued (~2-5 min)
4. `aws_route53_record.frontend` — A alias record: `coinbaby.click` → CloudFront distribution
5. Updated `aws_cloudfront_distribution.frontend`:
   - Added `aliases = ["coinbaby.click"]`
   - Swapped `cloudfront_default_certificate` for the ACM cert with `sni-only` and `TLSv1.2_2021`

All resources are conditional on `route53_zone_id` + `frontend_domain_name` being set.

**Other changes:**
- `variables.tf` — added `frontend_domain_name` variable
- `terraform.tfvars` — set `route53_zone_id` and `frontend_domain_name = "coinbaby.click"`

**IAM issue:** `dalla-project-owner` lacked `acm:RequestCertificate`. Fixed with an inline policy granting `acm:*` on `*`.

**Files Changed:**
- `infra/terraform/frontend.tf` — ACM cert, DNS validation, Route 53 alias, CloudFront aliases + viewer_certificate
- `infra/terraform/variables.tf` — added `frontend_domain_name`
- `infra/terraform/terraform.tfvars` — set domain vars
