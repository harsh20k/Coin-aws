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

3. **Model Upgrade Issue & Resolution:**
   - Initially attempted to upgrade from Claude 3 Haiku to Claude 4.5 Haiku
   - Claude 4.5 Haiku returned `ValidationException` - model not available/enabled in region
   - Switched to Claude 3.5 Haiku but got error: "Invocation of model ID with on-demand throughput isn't supported"
   - **Root cause**: Claude 3.5 Haiku requires using an inference profile, not direct model ID
   - **Final solution**: Use inference profile `us.anthropic.claude-3-5-haiku-20241022-v1:0` instead of direct model ID
   - Updated both `chat.py` and IAM permissions in `ec2.tf`

**Why These Changes:**
- Docker cleanup ensures deployments won't fail due to disk space, even with current 8GB disk
- Larger EBS volume provides breathing room for future growth and multiple image versions
- Claude 3.5 Haiku provides better performance than Claude 3 Haiku while maintaining cost efficiency
- Inference profiles enable cross-region routing and on-demand throughput for newer Claude models

**Files Changed:**
- `buildspec-backend-deploy.yml` - Added Docker cleanup step (removed `--volumes` flag for compatibility)
- `infra/terraform/ec2.tf` - Increased EBS volume + updated Bedrock IAM permissions to inference profile
- `backend/app/routers/chat.py` - Updated model ID to use inference profile format

**Next Steps:**
1. Commit and push changes to trigger CodeBuild
2. Run `terraform apply` to create new EC2 instance with 20GB disk and Claude 3.5 Haiku permissions
3. Verify deployment succeeds and `df -h` shows more free space on new instance
4. Test chat feature to confirm Claude 3.5 Haiku works via inference profile
