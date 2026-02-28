# Least-Privilege IAM Roles — How We Use It

## Principle

Each AWS service gets **one role** with **only the permissions it needs** to do its job. No shared “super” role, no `AdministratorAccess`, no broad `*` on resources where we can avoid it.

---

## Per-service breakdown

### EC2 (backend instance)

- **SSM Parameter Store (read):** `ssm:GetParameter`, `GetParameters`, `GetParametersByPath` — so the deploy script on the instance can read DATABASE_URL and Cognito params. (Resources: `*` in our Terraform; could be scoped to `/dalla/prod/*`.)
- **ECR (read):** attached managed policy `AmazonEC2ContainerRegistryReadOnly` — pull backend image only.
- **SSM Run Command (receive):** attached `AmazonSSMManagedInstanceCore` — lets the pipeline run scripts on the instance; no SSH.
- **Bedrock:** custom policy — `bedrock:InvokeModel`, `bedrock:GetInferenceProfile` on foundation-model and inference-profile ARNs only (for AI chat).

No write to S3, no SendCommand, no other services.

### CodeBuild (pipeline build/deploy)

- **Logs:** `logs:CreateLogGroup`, `CreateLogStream`, `PutLogEvents` (for build logs).
- **S3 (artifacts):** Get/Put/List/Delete on the **pipeline artifacts bucket** only, not the frontend bucket (except where frontend build needs it — see below).
- **ECR:** `GetAuthorizationToken` (any); Put/BatchGet/InitiateLayerUpload etc. on **this project’s ECR repository** only.
- **SSM SendCommand:** on **this backend instance** and the document `AWS-RunShellScript` only.
- **SSM GetCommandInvocation:** to poll deploy status (resources `*`; required by the API).
- **SSM GetParameter/GetParameters:** on **`/dalla/prod/*`** only (frontend and deploy scripts need API URL and Cognito params).
- **S3 (frontend):** Put/Get/List/Delete on the **frontend bucket** only (for frontend build sync).
- **CloudFront:** `CreateInvalidation`, `GetDistribution` on **this distribution** only.
- **EC2:** `DescribeInstances`, `DescribeInstanceStatus` (to get instance ID for SendCommand).

No CodeCommit write, no other ECR repos, no other S3 buckets or distributions.

### CodePipeline

- **S3:** Get/Put/GetBucketLocation on the **pipeline artifacts bucket** only.
- **CodeCommit:** read and `UploadArchive` on **this repo** only.
- **CodeBuild:** `BatchGetBuilds`, `StartBuild` (to trigger builds).

No direct EC2/SSM/ECR/S3 frontend access; it only orchestrates CodeBuild.

### Lambda (Cognito pre-sign-up)

- **AWSLambdaBasicExecutionRole** only — CloudWatch Logs for the function. The trigger only returns a modified event (autoConfirmUser, autoVerifyEmail); Cognito does the rest. No Cognito API calls from the Lambda, so no extra Cognito permissions.

---

## Choices that enforce least privilege

- **Separate roles per service** — EC2, CodeBuild, CodePipeline, Lambda each have their own role; a compromise in one doesn’t grant the others’ permissions.
- **Resource-level scoping** — SSM parameters limited to `parameter/${local.project_name}/prod/*`; ECR and S3 to this project’s resources; CloudFront to this distribution.
- **Action-level scoping** — Only the SSM actions we need (SendCommand + GetCommandInvocation, GetParameter(s)); only the ECR actions for push/pull; no `ecr:*` or `ssm:*`.
- **No long-lived keys** — All of the above use **IAM roles** (instance profile for EC2; service role for CodeBuild/CodePipeline/Lambda). No access keys in code or config.
- **Managed policies only where they match** — We use `AmazonEC2ContainerRegistryReadOnly` and `AmazonSSMManagedInstanceCore` because they match exactly what the instance needs; custom policies for SSM (read) and Bedrock.

---

## One-line summary

Every role is scoped to the minimum set of actions and resources needed for that service (SSM read, ECR pull, Bedrock invoke, pipeline artifacts, deploy, frontend bucket, etc.); no admin, no wildcard beyond what the APIs require.


IAM is implemented as follows: each AWS service (EC2, CodeBuild, CodePipeline, Lambda) uses a dedicated IAM role with only the specific permissions it needs—no long-lived access keys are created or stored anywhere. Roles are scoped for least privilege in Terraform. Wildcard resource permissions (`*`) are avoided except where the API requires it (e.g. `ssm:GetCommandInvocation`).

| Role | Used by | Permissions (rights) |
|------|---------|----------------------|
| **Backend (EC2)** | Backend instance profile | SSM: GetParameter, GetParameters, GetParametersByPath (read config at deploy). ECR: read-only (pull backend image). SSM: AmazonSSMManagedInstanceCore (receive Run Command from pipeline). Bedrock: InvokeModel, GetInferenceProfile on foundation-model/inference-profile ARNs only. |
| **CodeBuild** | All three CodeBuild projects (backend build, backend deploy, frontend build) | Logs: CreateLogGroup, CreateLogStream, PutLogEvents. S3: Get/Put/List/Delete on pipeline artifacts bucket and frontend bucket. ECR: GetAuthorizationToken; push/pull on this project’s ECR repo only. SSM: SendCommand on backend instance + AWS-RunShellScript doc; GetCommandInvocation; GetParameter(s) on `/dalla/prod/*` only. CloudFront: CreateInvalidation, GetDistribution on frontend distribution. EC2: DescribeInstances, DescribeInstanceStatus. |
| **CodePipeline** | Pipeline orchestration | S3: Get/Put/GetBucketLocation on pipeline artifacts bucket. CodeCommit: GetBranch, GetCommit, GetRepository, ListBranches, UploadArchive, GetUploadArchiveStatus on this repo. CodeBuild: BatchGetBuilds, StartBuild. |
| **Lambda (Cognito trigger)** | Pre-sign-up Lambda | AWSLambdaBasicExecutionRole only (CloudWatch Logs). Trigger returns event with autoConfirmUser/autoVerifyEmail; no Cognito API calls from Lambda. |