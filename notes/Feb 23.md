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

---

## Issue: Backend Container Crashes Due to Missing Database Tables

### Problem
After fixing SSM agent issue and deploying successfully, backend container crashed immediately on startup. Backend API was unreachable at `http://54.224.40.118:8000`.

### Investigation
```bash
# Container not running
sudo docker ps
CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES

# Container logs showed database error
sudo docker logs backend
ERROR: relation "subcategories" does not exist
ERROR: Application startup failed. Exiting.
```

### Root Cause
Backend's startup lifespan function tries to seed default subcategories, but RDS database is empty (no tables created yet). The backend crashes instead of handling missing tables gracefully.

```python
# app/main.py - crashes on startup if tables don't exist
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with get_session() as session:
        await seed_default_subcategories_session(session)  # Crashes here
    yield
```

### Why Previous Fixes Didn't Help
1. **SSM Agent Installation**: Fixed command delivery to EC2, but container still crashed after successful deployment
2. **Removing user_data deployment**: Fixed timing issues, but didn't address missing database schema
3. **Pipeline shows "Success"**: SSM command successfully pulled image and started container, but container immediately crashed

The deployment infrastructure worked correctly - the application itself had a missing dependency (database schema).

### Solution
Updated `buildspec-backend-deploy.yml` to create database tables **before** starting the backend container:

```yaml
# Run table creation as a one-off container
sudo docker run --rm -e DATABASE_URL="$DATABASE_URL" __ECR_URI__ python -m scripts.create_tables

# Then start the backend container
sudo docker run -d --name backend ...
```

This ensures:
- Tables are created/updated on every deployment (idempotent)
- Backend container never starts without required schema
- No manual database setup needed

### Lessons Learned
- Backend should handle missing tables gracefully (auto-create or fail with clear error)
- Database migrations should be part of deployment automation
- Container "running" status doesn't mean application is healthy - need health checks

---

## Issue: SSM Command Still Stuck in Pending After Infrastructure Rebuild

### Problem
After running `terraform destroy` and `terraform apply`, the DeployBackend stage was still stuck in Pending status, even though SSM agent was confirmed online and registered.

### Investigation
```bash
# Confirmed SSM agent is online and registered
aws ssm describe-instance-information --region us-east-1
{
    "InstanceInformationList": [{
        "InstanceId": "i-0a331b6e7a801f6e0",
        "PingStatus": "Online",
        "AgentVersion": "3.3.1957.0",
        ...
    }]
}

# Confirmed terraform has correct instance ID
terraform output backend_instance_id
i-0a331b6e7a801f6e0

# Both match - so why is command stuck in Pending?
```

### Root Cause
**Missing IAM Permission**: CodeBuild IAM role had permission to send SSM commands (`ssm:SendCommand`) but was missing permission to check command status (`ssm:GetCommandInvocation`).

The buildspec calls:
```bash
aws ssm get-command-invocation --command-id $CMD_ID --instance-id $BACKEND_INSTANCE_ID
```

But CodeBuild's IAM role only allowed `ssm:SendCommand`. Without `ssm:GetCommandInvocation` permission, the status check fails silently or returns an error, causing the build to hang waiting for a status that it can't retrieve.

### Solution
Updated `/infra/terraform/codepipeline.tf` to add missing SSM permission:

```terraform
statement {
  sid    = "SSMSendCommand"
  effect = "Allow"
  actions = [
    "ssm:SendCommand",
    "ssm:GetCommandInvocation"  # Added this permission
  ]
  resources = [
    "arn:aws:ec2:${var.aws_region}:${data.aws_caller_identity.current.account_id}:instance/${aws_instance.backend.id}",
    "arn:aws:ssm:${var.aws_region}::document/AWS-RunShellScript"
  ]
}
```

After running `terraform apply` to update IAM permissions, retry the pipeline.

### Initial Solution Attempt
Updated `/infra/terraform/codepipeline.tf` to add missing SSM permission:

```terraform
statement {
  sid    = "SSMSendCommand"
  effect = "Allow"
  actions = [
    "ssm:SendCommand",
    "ssm:GetCommandInvocation"  # Added this permission
  ]
  resources = [
    "arn:aws:ec2:${var.aws_region}:${data.aws_caller_identity.current.account_id}:instance/${aws_instance.backend.id}",
    "arn:aws:ssm:${var.aws_region}::document/AWS-RunShellScript"
  ]
}
```

**Result**: Still failed! Applied `terraform apply` but issue persisted.

---

## Final Root Cause: IAM Resource Constraint Issue

### The Real Problem
After multiple troubleshooting attempts (SSM agent installation, removing user_data deployment, adding database migrations, adding IAM permissions), the issue **still persisted**. 

### Systematic Debug Approach
Added instrumentation to `buildspec-backend-deploy.yml` to capture runtime evidence:
- Tested if `get-command-invocation` API works
- Captured full error messages (which were being silently suppressed by `2>/dev/null`)
- Monitored SSM agent health status

### Debug Output Revealed the Truth
```bash
[DEBUG-H1] Raw API response: 
An error occurred (AccessDeniedException) when calling the GetCommandInvocation operation: 
User: arn:aws:sts::411960113601:assumed-role/dalla-codebuild-role/... 
is not authorized to perform: ssm:GetCommandInvocation on resource: arn:aws:ssm:us-east-1:411960113601:* 
because no identity-based policy allows the ssm:GetCommandInvocation action
```

### Actual Root Cause
**Incorrect IAM Resource Constraint**: The `ssm:GetCommandInvocation` permission was added, but it was scoped to the wrong resources:
- **Allowed resources**: `arn:aws:ec2:...:instance/...` and `arn:aws:ssm:...:document/...`  
- **Required resources**: `*` (command invocations use dynamic ARNs that can't be predicted)

The `get-command-invocation` API tries to access `arn:aws:ssm:us-east-1:411960113601:*`, which didn't match the restrictive resource list. The `2>/dev/null` in the buildspec was silently hiding this error.

### The Fix That Actually Worked
Split SSM permissions into two separate statements in `/infra/terraform/codepipeline.tf`:

```terraform
# Scoped permission for sending commands
statement {
  sid    = "SSMSendCommand"
  effect = "Allow"
  actions = ["ssm:SendCommand"]
  resources = [
    "arn:aws:ec2:${var.aws_region}:${data.aws_caller_identity.current.account_id}:instance/${aws_instance.backend.id}",
    "arn:aws:ssm:${var.aws_region}::document/AWS-RunShellScript"
  ]
}

# Wildcard permission for checking command status
statement {
  sid    = "SSMGetCommandInvocation"
  effect = "Allow"
  actions = ["ssm:GetCommandInvocation"]
  resources = ["*"]
}
```

### Verification
After `terraform apply`:
- **Iteration 1**: Status changed from "Pending" to "InProgress" ✓
- **Iteration 2**: Status "Success" ✓  
- **Total deployment time**: ~15 seconds (was timing out at 15 minutes before)
- Backend container successfully deployed and running

### Key Lessons Learned
1. **Error suppression is dangerous**: The `2>/dev/null` in buildspec hid critical IAM permission errors, making debugging extremely difficult
2. **IAM resource constraints matter**: Adding an action to a policy isn't enough - the resources must match what the API actually accesses
3. **Runtime evidence is essential**: Static code analysis couldn't reveal this; only runtime debugging with actual error messages exposed the real issue
4. **Different AWS APIs have different resource requirements**: `SendCommand` can be scoped to specific instances/documents, but `GetCommandInvocation` needs wildcard access
5. **Systematic debugging pays off**: After 3 failed fix attempts, adding instrumentation to capture runtime data immediately revealed the true root cause
6. **IAM permission scope varies by action**: Not all actions in the same service (SSM) require the same resource constraints
7. **Silent failures in automation are the hardest to debug**: The build appeared to work (command was sent) but status checks failed silently
