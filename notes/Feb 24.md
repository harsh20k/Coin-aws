## EC2 Disk Space Issue (Feb 24)

**Problem:** Backend deployment failing with `failed to register layer: write /usr/local/lib/python3.12/site-packages/sqlalchemy/sql/__pycache__/selectable.cpython-312.pyc: no space left on device` during Docker image pull.

**Root Cause:** 
- EC2 t3.micro instance with default 8GB EBS volume
- Docker consuming 5.3GB of 6.1GB total space in `/var`
- Old Docker images, containers, layers, and volumes accumulating over time
- No cleanup happening between deployments

**Solution:**

1. **Immediate Fix (buildspec-backend-deploy.yml):**
   - Added `sudo docker system prune -af --volumes --filter "until=24h"` before Docker pull
   - Removes all stopped containers, unused images, volumes, and build cache older than 24 hours
   - Runs automatically on each deployment to free up space

2. **Long-term Fix (ec2.tf):**
   - Added `root_block_device` configuration to increase EBS volume from 8GB to 20GB
   - Set volume type to `gp3` with encryption enabled
   - Requires `terraform apply` to create new instance with larger disk

3. **Model Upgrade (ec2.tf + chat.py):**
   - Upgraded from Claude 3 Haiku to Claude 4.5 Haiku (released Oct 2025)
   - Model ID: `anthropic.claude-haiku-4-5-20251001-v1:0`
   - Claude 4.5 Haiku delivers near-frontier performance comparable to Sonnet 4 but at lower cost and faster speed
   - Updated IAM Bedrock permissions and backend model invocation
   - Requires `terraform apply` to update IAM policy, then redeploy backend

**Why These Changes:**
- Docker cleanup ensures deployments won't fail due to disk space, even with current 8GB disk
- Larger EBS volume provides breathing room for future growth and multiple image versions
- Claude 4.5 Haiku provides significantly better performance than Claude 3 Haiku while maintaining cost efficiency

**Files Changed:**
- `buildspec-backend-deploy.yml` - Added Docker cleanup step
- `infra/terraform/ec2.tf` - Increased EBS volume + updated Bedrock IAM permissions
- `backend/app/routers/chat.py` - Updated model ID to Claude 4.5 Haiku

**Next Steps:**
1. Commit and push changes to trigger CodeBuild
2. Run `terraform apply` to create new EC2 instance with 20GB disk and Claude 4.5 permissions
3. Verify deployment succeeds and `df -h` shows more free space on new instance
