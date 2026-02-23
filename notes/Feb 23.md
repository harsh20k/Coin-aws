# Feb 23, 2026

## Issue: CodePipeline DeployBackend Stage Stuck in Pending

### Problem
Pipeline's DeployBackend stage was stuck waiting indefinitely with SSM command status showing "Pending" repeatedly.

### Root Causes
1. **SSM Agent Not Installed**: Ubuntu 20.04 doesn't have SSM agent pre-installed. The EC2 instance couldn't receive SSM commands from CodeBuild.
2. **Timing Issue**: EC2 user_data tried to pull Docker image immediately on instance creation, but the image didn't exist in ECR yet (pipeline builds it later).

### Investigation
```bash
# SSM command stuck in pending
Status: Pending
Status: Pending
...

# On EC2 instance - no container running
sudo docker ps
CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES

# cloud-init log showed Docker pull failure
docker: Error response from daemon: manifest for 411960113601.dkr.ecr.us-east-1.amazonaws.com/dalla-backend:latest not found

# Image exists now (pushed later by pipeline)
aws ecr describe-images --repository-name dalla-backend --region us-east-1
```

### Solution
Updated `/infra/terraform/ec2.tf`:

1. **Added SSM Agent installation** to user_data:
   ```bash
   snap install amazon-ssm-agent --classic
   systemctl enable snap.amazon-ssm-agent.amazon-ssm-agent.service
   systemctl start snap.amazon-ssm-agent.amazon-ssm-agent.service
   ```

2. **Removed Docker container deployment** from user_data:
   - Removed ECR login, Docker pull, and container run commands
   - Let pipeline handle deployments via SSM instead
   - Removed `depends_on` block for SSM parameters (no longer needed in user_data)

### Deployment Flow
**Infrastructure First, Then Pipeline:**
1. `terraform apply` → Creates EC2 with Docker + SSM agent installed
2. `git push` → Pipeline builds image → Pushes to ECR → Deploys via SSM
3. Future pushes → Pipeline automatically rebuilds and redeploys

### Next Steps
- Run `terraform apply -replace="aws_instance.backend"` to recreate instance
- Verify SSM registration: `aws ssm describe-instance-information --region us-east-1`
- Retry pipeline deployment
