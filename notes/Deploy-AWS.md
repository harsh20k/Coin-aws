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
  **Easiest:** attach these managed policies to the Terraform user: **AmazonEC2FullAccess**, **IAMFullAccess**, **AmazonEC2ContainerRegistryFullAccess**, **AmazonS3FullAccess**, **CloudFrontFullAccess**, **AmazonCognitoPowerUser** (or FullAccess), **CloudWatchLogsFullAccess**, **AmazonRDSFullAccess**, **AmazonSSMFullAccess**. Alternatively use a single custom policy that includes the above actions (and any others this stack uses).

  **If you see `UnauthorizedOperation` for `ec2:DescribeImages` or `ec2:DescribeAvailabilityZones`:** the Terraform IAM user (e.g. `demo-user`) has no EC2 read policy. Attach **AmazonEC2FullAccess** to that user (or a custom policy that allows at least `ec2:DescribeImages` and `ec2:DescribeAvailabilityZones` on `*`).
- **EC2 key pair** in the target region (create in EC2 → Key Pairs).
- **`terraform.tfvars`** (copy from `terraform.tfvars.example`) with at least:
  - `aws_region`, `project_name`
  - `ec2_key_name` = that key pair name
  - `backend_image_uri` = ECR URI (see step 3)
  - `aws_profile` = your named AWS CLI profile with deploy permissions (e.g. `dalla-project-owner`), or leave empty to use default credentials. Use the **same profile** for all `aws` commands below (ECR login, S3 sync, CloudFront).

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

This creates VPC, RDS, Cognito, ECR, backend EC2 with Elastic IP, S3, CloudFront, and SSM (including `DATABASE_URL` from RDS). The EC2 will only run the backend once the image exists (step 3). Backend is reached at `terraform output api_url` (e.g. `http://<eip>:8000`).

## 3. Backend image → ECR

From repo root. Use the same AWS profile as Terraform (e.g. `dalla-project-owner`); otherwise ECR login can fail with `AccessDeniedException` or `ecr:GetAuthorizationToken` if your default credentials lack ECR access.

```bash
# ECR login (set AWS_PROFILE to the profile you use for Terraform)
AWS_PROFILE=dalla-project-owner aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com

# Build for EC2 (linux/amd64). Required on Apple Silicon / arm64 Macs so the image runs on x86_64 EC2.
docker build --platform linux/amd64 -t dalla-backend ./backend
# Tag and push using the full ECR URL (replace <ACCOUNT_ID> with your account ID)
docker tag dalla-backend:latest <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/dalla-backend:latest
docker push <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/dalla-backend:latest
```
Replace `<ACCOUNT_ID>` with your AWS account ID (same as in the ECR login URL above). If you build on an arm64 Mac without `--platform linux/amd64`, EC2 will fail with "no matching manifest for linux/amd64".

Set the same URI in `terraform.tfvars` as `backend_image_uri`, then either run `terraform apply` again so the EC2 launch config uses it, or restart the instance so it pulls and runs the container.

## 4. Backend DB schema

RDS is created empty and is not publicly accessible. **Tables must exist before the backend app starts:** the app runs `seed_default_subcategories()` on startup, which requires the `subcategories` table. So run the table-creation script first (see below), then start or restart the backend.

From your machine (repo root or `infra/terraform`), SSH into the backend instance. Use the same key pair as `ec2_key_name` in `terraform.tfvars`; fix key permissions if SSH complains:

```bash
chmod 600 ~/.ssh/dalla-deploy.pem
cd infra/terraform
BACKEND_IP=$(terraform output -raw backend_public_ip)
ssh -i ~/.ssh/dalla-deploy.pem ubuntu@$BACKEND_IP
```

**If the backend container is already running**, create tables inside it:

```bash
sudo docker exec backend python -m scripts.create_tables
```

You should see `Tables created.`

**If no backend container is running** (e.g. user_data failed because the image wasn’t in ECR yet), create tables first with a **one-off** container, then start the backend. The instance role has ECR read access (Terraform attaches `AmazonEC2ContainerRegistryReadOnly`). From the EC2 instance:

```bash
aws ecr get-login-password --region us-east-1 | sudo docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com

REGION="us-east-1"
DATABASE_URL=$(aws ssm get-parameter --name "/dalla/prod/DATABASE_URL" --with-decryption --region "$REGION" --query "Parameter.Value" --output text)
COGNITO_REGION=$(aws ssm get-parameter --name "/dalla/prod/COGNITO_REGION" --with-decryption --region "$REGION" --query "Parameter.Value" --output text)
COGNITO_USER_POOL_ID=$(aws ssm get-parameter --name "/dalla/prod/COGNITO_USER_POOL_ID" --with-decryption --region "$REGION" --query "Parameter.Value" --output text)
COGNITO_APP_CLIENT_ID=$(aws ssm get-parameter --name "/dalla/prod/COGNITO_APP_CLIENT_ID" --with-decryption --region "$REGION" --query "Parameter.Value" --output text)

# 1. Create tables first (one-off container). Required before starting the app (app seeds subcategories on startup).
sudo docker run --rm \
  -e DATABASE_URL="$DATABASE_URL" \
  <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/dalla-backend:latest \
  python -m scripts.create_tables

# 2. Start the backend container (remove existing one if it exited)
sudo docker rm -f backend 2>/dev/null || true
sudo docker run -d \
  --name backend \
  -p 8000:8000 \
  -e DATABASE_URL="$DATABASE_URL" \
  -e COGNITO_REGION="$COGNITO_REGION" \
  -e COGNITO_USER_POOL_ID="$COGNITO_USER_POOL_ID" \
  -e COGNITO_APP_CLIENT_ID="$COGNITO_APP_CLIENT_ID" \
  411960113601.dkr.ecr.us-east-1.amazonaws.com/dalla-backend:latest
```
Replace `<ACCOUNT_ID>` with your AWS account ID. (using this command `aws sts get-caller-identity --query Account --output text`)

**If the backend container exits on startup** (e.g. `relation "subcategories" does not exist` in `sudo docker logs backend`), tables were missing. Run the one-off `create_tables` command above (step 1), then `sudo docker rm -f backend` and start the container again (step 2).

## 5. Frontend build and deploy

Terraform does **not** upload the frontend. You build and sync:

1. Use the **Terraform-created** Cognito pool and client for the build. Your local `.env` may point to a different pool (e.g. dev); the deployed app must use the same pool as the backend (from Terraform). Set:
   - `VITE_API_URL` from `terraform output api_url`
   - `VITE_COGNITO_USER_POOL_ID` from `terraform output user_pool_id`
   - `VITE_COGNITO_APP_CLIENT_ID` from `terraform output client_id`
   - `VITE_COGNITO_REGION` (e.g. `us-east-1`)
2. Build and sync:

```bash
cd frontend
TF_DIR=../infra/terraform
export VITE_API_URL=$(cd $TF_DIR && terraform output -raw api_url)
export VITE_COGNITO_USER_POOL_ID=$(cd $TF_DIR && terraform output -raw user_pool_id)
export VITE_COGNITO_APP_CLIENT_ID=$(cd $TF_DIR && terraform output -raw client_id)
export VITE_COGNITO_REGION=us-east-1
npm run build
AWS_PROFILE=dalla-project-owner aws s3 sync dist/ s3://$(cd $TF_DIR && terraform output -raw frontend_bucket_name) --delete
```

Invalidate CloudFront cache so changes are visible. Get the distribution ID (for the frontend origin), then create the invalidation:

```bash
# Get the CloudFront distribution ID for the frontend (replace placeholder if needed)
DIST_ID=$(AWS_PROFILE=dalla-project-owner aws cloudfront list-distributions --query "DistributionList.Items[?contains(Origins.Items[0].DomainName, 'dalla-frontend')].Id" --output text)
AWS_PROFILE=dalla-project-owner aws cloudfront create-invalidation --distribution-id $DIST_ID --paths "/*"
```

Alternatively, get the ID from AWS Console → CloudFront and pass it directly: `--distribution-id E2TLANCEPG0UPC` (use your actual ID).

## 6. Smoke test

- **Backend:** `terraform output api_url` → e.g. `GET /health`.
- **Frontend:** Open the app and sign in with Cognito. Use the **HTTP** URL so the browser allows calls to the HTTP backend (mixed-content workaround): change `https` to `http` in the CloudFront URL, e.g. `http://d3156omzi2icat.cloudfront.net` (or `terraform output cloudfront_url` then replace `https` with `http`). If you use the HTTPS URL, Wallets/API will show "Load failed" (see `notes/Feb 20.md`).

---

## Caveats

- **Build for EC2 architecture:** EC2 is x86_64 (linux/amd64). If you build the backend image on an Apple Silicon (arm64) Mac without `--platform linux/amd64`, the image will have no amd64 manifest and EC2 will fail with "no matching manifest for linux/amd64". Always use `docker build --platform linux/amd64` when building for AWS.
- EC2 user_data runs only once at first boot to set up Docker, fetch SSM params, and start the backend container. If any step fails (e.g. image not yet in ECR, ECR pull or SSM fetch fails), no container is created. Check `sudo cat /var/log/cloud-init-output.log` on EC2 to debug. The backend instance role has ECR read (`AmazonEC2ContainerRegistryReadOnly`) so the instance can pull the image once it is in ECR.
- Always push the backend image to ECR **before** (or right after) creating the EC2 instance. If you push later, user_data may have already failed, so you need to start the container manually (see step 4, "If no backend container is running") or replace the instance.
- **Mixed content:** The backend is HTTP; the frontend is on CloudFront. CloudFront is set to `viewer_protocol_policy = "allow-all"` so you can open the app via **http://** (CloudFront domain) and avoid browser blocking of HTTP API calls. Use the HTTP frontend URL when testing (see step 6).
- After `terraform destroy` + `terraform apply`, ECR is empty. Push the backend image again (with `--platform linux/amd64`), then either:
  - SSH into EC2, manually run the ECR login, `docker run` (with SSM env vars), and `create_tables` (see step 4), or
  - Replace the instance (`terraform taint aws_instance.backend` + `terraform apply`) after pushing the image, so user_data runs again and succeeds.

---

**Summary:** Fill `terraform.tfvars`, run `terraform apply`, build and push the backend image to the Terraform-created ECR, create DB tables, then build the frontend with the correct API URL and sync to the Terraform-created S3 bucket.
