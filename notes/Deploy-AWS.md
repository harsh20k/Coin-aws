# Run Dalla on AWS

Deploy the full app (backend + frontend) using the Terraform stack in `infra/terraform/`.

---

## Contents

1. [Prerequisites](#1-prerequisites)
2. [First Terraform apply](#2-first-terraform-apply)
3. [Push code to CodeCommit (CI/CD)](#3-push-code-to-codecommit-cicd)
4. [Backend DB schema](#4-backend-db-schema)
5. [Smoke test](#5-smoke-test)
6. [Caveats](#caveats)

---

## 1. Prerequisites

### IAM

The IAM user/role used for Terraform (e.g. `dalla-project-owner`) must be able to create and manage all stack resources. Missing permissions cause `AccessDenied` / `UnauthorizedOperation`.

**Required permissions (by service):**


| Service      | Needs                                                                                                         |
| ------------ | ------------------------------------------------------------------------------------------------------------- |
| EC2          | DescribeImages, DescribeAvailabilityZones, instances, security groups, launch templates, etc.                 |
| IAM          | CreateRole, CreatePolicy, AttachRolePolicy, PutRolePolicy, PassRole, GetRole, GetPolicy (instance role + SSM) |
| ECR          | CreateRepository, GetAuthorizationToken, push for backend image                                               |
| S3           | CreateBucket, PutBucketPolicy, PutObject, GetObject (frontend bucket)                                         |
| CloudFront   | CreateDistribution, CreateCloudFrontOriginAccessIdentity, Get*, etc.                                          |
| Cognito      | CreateUserPool, CreateUserPoolClient, read/update                                                             |
| CloudWatch   | CreateLogGroup, PutLogEvents, etc.                                                                            |
| RDS          | CreateDBInstance, CreateDBSubnetGroup, etc.                                                                   |
| SSM          | GetParameter, GetParameters, PutParameter (DeleteParameter for destroy); for `/dalla/prod/*`; SendCommand for pipeline deploy |
| CodeCommit   | CreateRepository, GetRepository, etc.                                                                         |
| CodeBuild    | CreateProject, StartBuild, etc.                                                                               |
| CodePipeline | CreatePipeline, GetPipeline, etc.                                                                              |


**Easiest:** attach these managed policies to the Terraform user (e.g. `dalla-project-owner`):

- AmazonEC2FullAccess  
- IAMFullAccess  
- AmazonEC2ContainerRegistryFullAccess  
- AmazonS3FullAccess  
- CloudFrontFullAccess  
- AmazonCognitoPowerUser (or FullAccess)  
- CloudWatchLogsFullAccess  
- AmazonRDSFullAccess  
- AmazonSSMFullAccess  
- **AWSCodeCommitFullAccess**  
- **AWSCodeBuildAdminAccess**  
- **AWSCodePipelineFullAccess**

**If you see `AccessDeniedException` for `codecommit:CreateRepository` or `codebuild:CreateProject`:** the Terraform user needs CodeCommit/CodeBuild/CodePipeline. Either attach the three managed policies (AWSCodeCommitFullAccess, AWSCodeBuildAdminAccess, AWSCodePipelineFullAccess), or—**if you get "The selected policies exceed this account's quota"** (AWS limits managed policies per user)—add a single **inline policy** instead: IAM → Users → your user → Add permissions → Create inline policy → JSON tab → paste the contents of `infra/terraform/iam-terraform-runner-codecommit-codebuild-codepipeline.json`, name it (e.g. `DallaCodeCommitCodeBuildCodePipeline`), then create and retry `terraform apply`.

**If you see `UnauthorizedOperation` for `ec2:DescribeImages` or `ec2:DescribeAvailabilityZones`:** attach **AmazonEC2FullAccess** (or a custom policy with at least those two actions on `*`) to the Terraform user.

### Other

- **EC2 key pair** in the target region (EC2 → Key Pairs).
- `**terraform.tfvars`** (from `terraform.tfvars.example`) with at least:
  - `aws_region`, `project_name`
  - `ec2_key_name` = key pair name
  - `backend_image_uri` = ECR URI (see step 3)
  - `aws_profile` = AWS CLI profile with deploy permissions (e.g. `dalla-project-owner`), or leave empty for default credentials.

Use the **same profile** for all `aws` commands (ECR login, S3 sync, CloudFront).

---

## 2. First Terraform apply

Set the ECR URI Terraform will create (replace account/region if needed):

```hcl
backend_image_uri = "<ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/dalla-backend:latest"
```

Get `<ACCOUNT_ID>`:

```bash
aws sts get-caller-identity --query Account --output text
```

Then:

```bash
cd infra/terraform
terraform init
terraform apply
```

**Creates:** VPC, RDS, Cognito, ECR, backend EC2 (Elastic IP), S3, CloudFront, SSM, **CodeCommit repo**, **CodeBuild projects**, and **CodePipeline**. Backend runs only after the image exists (pipeline build or one-time manual push, see below). API URL: `terraform output api_url` (e.g. `http://<eip>:8000`).

---

## 3. Push code to CodeCommit (CI/CD)

The pipeline builds and deploys automatically when you push to the CodeCommit repository.

### One-time: add CodeCommit as a remote and push

Get the clone URL from Terraform:

```bash
cd infra/terraform
terraform output codecommit_repository_https_url
# or for SSH: terraform output codecommit_repository_url
```

From your repo root (where you run git), add the remote and push. The pipeline watches the **main** branch by default (set `codecommit_branch` in Terraform to use another branch):

```bash
git remote add codecommit <PASTE_HTTPS_OR_SSH_URL>
git push codecommit main
```

(Use your default branch name if different, e.g. `master` — and set `codecommit_branch` in `terraform.tfvars` to match.)

**First run:** If the backend image is not in ECR yet, either run the pipeline once (it will build and push the image, then deploy), or push the image manually (see Caveats) and create DB tables (step 4) before the deploy step runs. The pipeline will: build backend image → push to ECR → run SSM Run Command on the backend EC2 to pull and restart the container → build frontend with SSM config → sync to S3 → invalidate CloudFront.

---

## 4. Backend DB schema

RDS is created empty and is not publicly accessible. **Tables must exist before the backend starts** — the app runs `seed_default_subcategories()` on startup and needs the `subcategories` table. Run the table-creation script first, then start/restart the backend.

### SSH into the backend

From repo root or `infra/terraform` (same key as `ec2_key_name`):

```bash
chmod 600 ~/.ssh/dalla-deploy.pem
cd infra/terraform
BACKEND_IP=$(terraform output -raw backend_public_ip)
ssh -i ~/.ssh/dalla-deploy.pem ubuntu@$BACKEND_IP
```

### Case A: Backend container already running

Create tables inside it:

```bash
sudo docker exec backend python -m scripts.create_tables
```

You should see `Tables created.`

### Case B: No backend container running

(e.g. user_data failed because the image wasn’t in ECR yet.) Create tables with a one-off container, then start the backend. Instance role has ECR read (Terraform attaches `AmazonEC2ContainerRegistryReadOnly`). On the EC2 instance:

```bash
aws ecr get-login-password --region us-east-1 | sudo docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com

REGION="us-east-1"
DATABASE_URL=$(aws ssm get-parameter --name "/dalla/prod/DATABASE_URL" --with-decryption --region "$REGION" --query "Parameter.Value" --output text)
COGNITO_REGION=$(aws ssm get-parameter --name "/dalla/prod/COGNITO_REGION" --with-decryption --region "$REGION" --query "Parameter.Value" --output text)
COGNITO_USER_POOL_ID=$(aws ssm get-parameter --name "/dalla/prod/COGNITO_USER_POOL_ID" --with-decryption --region "$REGION" --query "Parameter.Value" --output text)
COGNITO_APP_CLIENT_ID=$(aws ssm get-parameter --name "/dalla/prod/COGNITO_APP_CLIENT_ID" --with-decryption --region "$REGION" --query "Parameter.Value" --output text)

# 1. Create tables (one-off). Required before starting the app.
sudo docker run --rm \
  -e DATABASE_URL="$DATABASE_URL" \
  <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/dalla-backend:latest \
  python -m scripts.create_tables

# 2. Start the backend container
sudo docker rm -f backend 2>/dev/null || true
sudo docker run -d \
  --name backend \
  -p 8000:8000 \
  -e DATABASE_URL="$DATABASE_URL" \
  -e COGNITO_REGION="$COGNITO_REGION" \
  -e COGNITO_USER_POOL_ID="$COGNITO_USER_POOL_ID" \
  -e COGNITO_APP_CLIENT_ID="$COGNITO_APP_CLIENT_ID" \
  <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/dalla-backend:latest
```

Replace `<ACCOUNT_ID>` with your account ID (`aws sts get-caller-identity --query Account --output text`).

**If the backend container exits on startup** (e.g. `relation "subcategories" does not exist` in `sudo docker logs backend`): run the one-off `create_tables` (step 1), then remove and restart the container (step 2).

**First deploy:** If the database is new, run `create_tables` once (Case A or B above) before or right after the first pipeline run; otherwise the backend container may exit until tables exist.

---

## 5. Smoke test

- **Backend:** `terraform output api_url` → e.g. `GET /health`.
- **Frontend:** Open the app and sign in with Cognito. Use the **HTTP** URL so the browser allows calls to the HTTP backend (mixed-content): change `https` to `http` in the CloudFront URL (e.g. `http://d3156omzi2icat.cloudfront.net`). If you use HTTPS, Wallets/API may show "Load failed" (see `notes/Feb 20.md`).

---

## Caveats

- **EC2 architecture:** EC2 is x86_64. On Apple Silicon (arm64) always use `docker build --platform linux/amd64`; otherwise EC2 fails with "no matching manifest for linux/amd64".
- **user_data:** Runs only once at first boot (Docker, SSM params, backend container). If a step fails (image not in ECR, ECR pull or SSM fail), no container is created. Check `sudo cat /var/log/cloud-init-output.log` on EC2.
- **Image before instance:** Push the backend image to ECR before (or right after) creating the EC2 instance. If you push later, user_data may have already failed; start the container manually (step 4, Case B) or replace the instance.
- **Mixed content:** Backend is HTTP, frontend on CloudFront. CloudFront is `viewer_protocol_policy = "allow-all"` so you can open the app via **http://** (CloudFront domain) and avoid blocked HTTP API calls. Use the HTTP frontend URL when testing (step 6).
- **After destroy + apply:** ECR is empty. Either run the pipeline (it will build and push the image, then deploy) or push the backend image manually (`--platform linux/amd64`), then SSH and run ECR login + `docker run` + `create_tables` (step 4), or replace the instance (`terraform taint aws_instance.backend` + `terraform apply`) so user_data runs again.
- **RDS master password:** RDS disallows `/`, `@`, `"`, and space in the master password. The Terraform `random_password` for RDS uses `override_special` so only allowed specials (e.g. `!#$%&*()-_=+[]{}<>:?`) are used. If you see `InvalidParameterValue` for `MasterUserPassword`, ensure `rds.tf` has that override (see `notes/Feb 20.md`).
- **DATABASE_URL password encoding:** The `override_special` characters include URL-special chars (`#`, `%`, `?`, `:`). The password in `database_url` must be wrapped with `urlencode()` — otherwise these chars corrupt the connection string and cause `InvalidPasswordError`. If you see `asyncpg.exceptions.InvalidPasswordError: password authentication failed`, check that `rds.tf` uses `urlencode(random_password.db_password.result)` in the `database_url` local (see `notes/Feb 25.md`).

---

**Summary:** Fill `terraform.tfvars` → `terraform apply` → add CodeCommit as remote and `git push codecommit main` → pipeline builds backend, deploys to EC2, builds frontend and deploys to S3/CloudFront. Create DB tables once if the database is new (step 4).