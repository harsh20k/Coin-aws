## CodeCommit + CodeBuild + CodePipeline CI/CD (Feb 22)

**Goal:** When code is pushed to AWS CodeCommit, the pipeline automatically builds and deploys backend (ECR → EC2) and frontend (S3 + CloudFront). No manual ECR push or S3 sync.

**Implementation**

1. **SSM + EC2 (ec2.tf)**
   - Added `AmazonSSMManagedInstanceCore` to backend instance role so SSM Run Command can run deploy scripts on the instance.
   - Added variable `ssm_api_url_parameter_name` (default `/dalla/prod/API_URL`).
   - Added `aws_ssm_parameter.api_url` with value = `api_url` (EIP or Route53) for frontend build.

2. **CodePipeline stack (codepipeline.tf, new)**
   - **CodeCommit:** `aws_codecommit_repository.main` (name = `local.project_name`). Outputs: `codecommit_repository_url`, `codecommit_repository_https_url`.
   - **Artifacts:** S3 bucket for pipeline artifacts (versioning + AES256).
   - **IAM:** CodePipeline role (CodeCommit, S3, CodeBuild); CodeBuild role (ECR push, SSM SendCommand/GetParameter, S3 frontend, CloudFront invalidation, EC2 describe).
   - **CodeBuild projects:** `backend_build` (Docker build + ECR push), `backend_deploy` (SSM send-command to pull and restart container), `frontend_build` (SSM params → npm build → S3 sync → CloudFront invalidation).
   - **CodePipeline:** Source = CodeCommit (branch `codecommit_branch`, default `main`); stages: Source → BuildBackend → DeployBackend → BuildFrontend.

3. **Buildspecs (repo root)**
   - **buildspec-backend.yml:** ECR login, `docker build --platform linux/amd64 ./backend`, tag and push to ECR.
   - **buildspec-backend-deploy.yml:** Build script (ECR login, pull, stop/rm container, `docker run` with env from SSM); pass to EC2 via `aws ssm send-command`; wait for completion.
   - **buildspec-frontend.yml:** Read API URL and Cognito params from SSM, `npm ci` + `npm run build` in `frontend/`, `aws s3 sync dist/`, CloudFront invalidation.

4. **Docs (notes/Deploy-AWS.md)**
   - Prerequisites: added CodeCommit, CodeBuild, CodePipeline, SSM SendCommand.
   - Replaced “Backend image → ECR” and “Frontend build and deploy” with “Push code to CodeCommit (CI/CD)”: add remote, push to `main` (or set `codecommit_branch`).
   - Noted first deploy may require one-time `create_tables` if DB is new.
   - Summary updated to pipeline-based flow.

**Usage**

- `terraform apply` (with CodeCommit/CodeBuild/CodePipeline permissions).
- Add CodeCommit remote: `git remote add codecommit $(cd infra/terraform && terraform output -raw codecommit_repository_https_url)` (or SSH output).
- Push: `git push codecommit main`.
- Pipeline runs: build backend → push ECR → deploy backend (SSM on EC2) → build frontend → S3 sync + CloudFront invalidation.

**Variables**

- `codecommit_branch` (codepipeline.tf, default `main`) — branch that triggers the pipeline.
