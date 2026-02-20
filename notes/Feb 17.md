## Dalla Docker local run (Feb 17)

- **Prepare env files**
  - `cp backend/.env.example backend/.env` and set Cognito vars (`COGNITO_USER_POOL_ID`, `COGNITO_APP_CLIENT_ID`, optional `COGNITO_REGION`).
  - Optionally set `DATABASE_URL=postgresql+asyncpg://dalla:dalla@db:5432/dalla` for Docker.
  - `cp frontend/.env.example frontend/.env`, set Cognito vars, and for Docker set **`VITE_API_URL=http://localhost:8000`** (browser must call backend via `localhost`, not `backend`).

- **Start stack (db + backend + frontend)**
  - From repo root: `docker compose up --build`

- **Initialize DB schema (first run only)**
  - `docker compose exec backend python -m scripts.create_tables`

- **Access**
  - Backend docs: `http://localhost:8000/docs`
  - Frontend SPA: `http://localhost:5173`

- **Stop everything**
  - `docker compose down`

- **Gotcha: wallets/transactions “Load failed”**
  - **Symptom**: After login, wallets and transactions screens show **“Load failed”** and nothing can be created.
  - **Root cause**: Frontend `VITE_API_URL` pointing at `http://backend:8000` (a Docker-only hostname) instead of `http://localhost:8000`, plus an override in `docker-compose.yml` (`frontend.environment.VITE_API_URL`).
  - **Fix**: Set `VITE_API_URL=http://localhost:8000` in `frontend/.env`, remove the `VITE_API_URL` override from `docker-compose.yml`, then `docker compose down && docker compose build frontend && docker compose up`.

## Deployment decision (cloud)

- **Choice**: Run two Docker images (frontend + backend) on **ECS with Fargate**, and use **RDS** for PostgreSQL. For the first demo we can skip ALB (public IP on services) and add **ALB** later for a cleaner, production-style setup.

- **ECS**: Container orchestration service that runs and manages tasks/services (our frontend and backend containers).
- **Fargate**: Serverless compute for containers; runs ECS tasks without managing EC2 instances.
- **RDS (PostgreSQL)**: Managed relational database replacing the local Postgres container in the cloud.
- **ALB (optional)**: Application Load Balancer that provides a stable HTTPS endpoint and routes traffic to one or more ECS services.

## Cloud deployment steps (Terraform, EC2 + RDS + S3 + CloudFront)

- **Terraform project** (`infra/terraform`)
  - Defined providers (`aws`, `random`), shared `aws_region` / `project_name` variables, and Cognito pool + app client outputs for the app.
  - Added `terraform.tfvars.example` documenting required values (`backend_image_uri`, `ec2_key_name`, optional Route 53 + frontend bucket name).

- **Networking + security**
  - Created a VPC with two public subnets, internet gateway, and public route table.
  - Added security groups for ALB (HTTP from internet), backend EC2 (traffic from ALB + SSH CIDR), and RDS (Postgres only from backend SG).

- **Database (RDS Postgres)**
  - Provisioned a Postgres 16 RDS instance in the VPC with a generated strong password.
  - Exposed a `database_url` local and Terraform output in SQLAlchemy format (`postgresql+asyncpg://.../dalla`).

- **Backend compute (EC2 + Docker)**
  - Created an ECR repo for the backend image and an EC2 instance (Ubuntu) in a public subnet.
  - Attached an IAM role/instance profile allowing reads from SSM Parameter Store / Secrets Manager.
  - Used `user_data` to install Docker + AWS CLI, read `DATABASE_URL` and Cognito vars from SSM, and `docker run` the backend container on port 8000.

- **ALB + DNS**
  - Added an Application Load Balancer across public subnets, with a target group for the backend on port 8000 and a `/health` HTTP health check.
  - Wired a listener on port 80 that forwards traffic to the target group.
  - Optionally support a Route 53 `A` record (e.g. `api.dalla.example.com`) pointing to the ALB via alias.

- **Config + secrets (SSM Parameter Store)**
  - Created SSM parameters for `DATABASE_URL` and Cognito settings (region, user pool ID, app client ID) using Terraform.
  - Ensured the backend EC2 instance depends on these parameters so they exist before `user_data` runs.

- **Frontend hosting (S3 + CloudFront)**
  - Created a private S3 bucket for built frontend assets and a CloudFront distribution with an Origin Access Identity (OAI).
  - Configured SPA-friendly error handling (403/404 → `index.html`) and exposed outputs for the CloudFront URL and frontend bucket name.
  - Added an output noting that `VITE_API_URL` should be set to the backend ALB/API URL when running `npm run build` for production.

- **Monitoring**
  - Defined a CloudWatch log group for backend logs (for use by EC2/uvicorn).
  - Added basic CloudWatch alarms for high EC2 CPU, high RDS CPU, and ALB 5xx error count.
