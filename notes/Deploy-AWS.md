# Run Dalla on AWS

Steps to deploy and run the full app (backend + frontend) on AWS using the Terraform stack in `infra/terraform/`.

## 1. Prerequisites

- **IAM user/role** used for `terraform` (e.g. `dalla-project-owner`) must allow creating and managing all resources this stack uses. If permissions are missing, apply fails with `AccessDenied` / `UnauthorizedOperation`. This stack needs at least:
  - **EC2**: DescribeImages, DescribeAvailabilityZones, plus create/manage instances, security groups, launch templates, etc.
  - **IAM**: CreateRole, CreatePolicy, AttachRolePolicy, PutRolePolicy, PassRole, GetRole, GetPolicy, etc. (for backend instance role and SSM access).
  - **ECR**: CreateRepository, GetAuthorizationToken, and push permissions for the backend image.
  - **S3**: CreateBucket, PutBucketPolicy, PutObject, GetObject, etc. (frontend bucket).
  - **CloudFront**: CreateDistribution, CreateCloudFrontOriginAccessIdentity, Get*, etc.
  - **Cognito**: CreateUserPool, CreateUserPoolClient, and related read/update.
  - **CloudWatch Logs**: CreateLogGroup, PutLogEvents, etc.
  - **RDS**: CreateDBInstance, CreateDBSubnetGroup, etc.
  - **SSM**: GetParameter, GetParameters, PutParameter (and DeleteParameter if you destroy); required for `/dalla/prod/*` (Terraform reads and writes).
  - **ELB/ALB**: CreateLoadBalancer, CreateTargetGroup, CreateListener, etc.
  **Easiest:** attach these managed policies to the Terraform user: **AmazonEC2FullAccess**, **IAMFullAccess**, **AmazonEC2ContainerRegistryFullAccess**, **AmazonS3FullAccess**, **CloudFrontFullAccess**, **AmazonCognitoPowerUser** (or FullAccess), **CloudWatchLogsFullAccess**, **AmazonRDSFullAccess**, **AmazonSSMFullAccess**, **ElasticLoadBalancingFullAccess**. Alternatively use a single custom policy that includes the above actions (and any others this stack uses).
- **EC2 key pair** in the target region (create in EC2 → Key Pairs).
- **`terraform.tfvars`** (copy from `terraform.tfvars.example`) with at least:
  - `aws_region`, `project_name`
  - `ec2_key_name` = that key pair name
  - `backend_image_uri` = ECR URI (see step 3)

## 2. First Terraform apply

Use the ECR URI Terraform will create (replace account/region if needed):

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

This creates VPC, RDS, Cognito, ECR, ALB, EC2, S3, CloudFront, and SSM (including `DATABASE_URL` from RDS). The EC2 will only run the backend once the image exists (step 3).

## 3. Backend image → ECR

From repo root:

```bash
# ECR login
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com

# Build and push (use backend_ecr_repository_url from terraform output)
ECR_URL=$(cd infra/terraform && terraform output -raw backend_ecr_repository_url)
docker build -t dalla-backend ./backend
docker tag dalla-backend:latest $ECR_URL:latest
docker push $ECR_URL:latest
```

Set the same URI in `terraform.tfvars` as `backend_image_uri`, then either run `terraform apply` again so the EC2 launch config uses it, or restart the instance so it pulls and runs the container.

## 4. Backend DB schema

RDS is created empty. Run your table-creation script once against the deployed DB:

- Get `DATABASE_URL` from Terraform: `terraform output -raw database_url` (or from SSM `/dalla/prod/DATABASE_URL`).
- Run e.g. `python -m scripts.create_tables` with that `DATABASE_URL` (from a machine that can reach RDS, or a one-off task).

## 5. Frontend build and deploy

Terraform does **not** upload the frontend. You build and sync:

1. Set `VITE_API_URL` to the backend URL (ALB or custom domain), e.g. from `terraform output api_url` (or `frontend_api_url_placeholder`).
2. Build and sync:

```bash
cd frontend
# .env or env: VITE_API_URL=https://<alb-dns-or-api-domain> VITE_COGNITO_*=...
npm run build
aws s3 sync dist/ s3://$(cd ../infra/terraform && terraform output -raw frontend_bucket_name) --delete
```

Invalidate CloudFront cache so changes are visible:

```bash
aws cloudfront create-invalidation --distribution-id <distribution_id> --paths "/*"
```

(`distribution_id` is in AWS Console → CloudFront or add a Terraform output.)

## 6. Smoke test

- **Backend:** `terraform output api_url` → e.g. `GET /health`.
- **Frontend:** `terraform output cloudfront_url` → open in browser and sign in with Cognito.

---

**Summary:** Fill `terraform.tfvars`, run `terraform apply`, build and push the backend image to the Terraform-created ECR, create DB tables, then build the frontend with the correct API URL and sync to the Terraform-created S3 bucket.
