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
