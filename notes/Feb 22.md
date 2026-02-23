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

---

## Issues encountered (Feb 22–23)

1. **CodeCommit push asking for username/password**
   - **Cause:** Remote was set to HTTPS URL (`codecommit_repository_https_url`). HTTPS does not use SSH keys.
   - **Fix:** Use SSH URL: `git remote set-url aws $(cd infra/terraform && terraform output -raw codecommit_repository_url)`. Ensure `~/.ssh/config` has a Host for `git-codecommit.<region>.amazonaws.com` with `User` = IAM SSH key ID and `IdentityFile` = path to private key.

2. **Access denied: codecommit:GitPush**
   - **Cause:** IAM user (e.g. `dalla-project-owner`) had CodeCommit permissions for Terraform (CreateRepository, GetRepository, etc.) but not for git operations.
   - **Fix:** Added to inline policy (source: `infra/terraform/iam-terraform-runner-codecommit-codebuild-codepipeline.json`): `codecommit:GitPush`, `codecommit:GitPull`, `codecommit:GetBranch`, `codecommit:GetCommit`, `codecommit:ListBranches`. Apply by updating the IAM user’s inline policy in the console with the JSON from that file.

3. **Deploy Backend stage: YAML_FILE_ERROR at line 22**
   - **Cause:** In `buildspec-backend-deploy.yml`, a `commands` list item contained unquoted `{'commands': [sys.stdin.read()]}`. The YAML parser (CodeBuild and some local parsers) treated `{...}` as a flow mapping and expected a key, failing at the next line.
   - **Fix:** Put the Python one-liner in a literal block (`- |` with indented content) so the braces are never parsed as YAML. Also increased indentation of other literal-block contents for consistent parsing. No `terraform apply` needed—fix is in repo; use a **new** pipeline run (not “re-run” of an old execution) so the stage gets the updated buildspec from Source.

4. **Deploy Backend: AccessDeniedException on ssm:SendCommand**
   - **Cause:** CodeBuild role had `ssm:SendCommand` only on the EC2 instance resource. AWS requires the same action on the **SSM document** resource (`arn:aws:ssm:region::document/AWS-RunShellScript`) when using Run Command.
   - **Fix:** In `codepipeline.tf`, in the CodeBuild IAM policy's SSMSendCommand statement, add the document ARN to `resources`: `arn:aws:ssm:${var.aws_region}::document/AWS-RunShellScript`. Then run `terraform apply`; re-run the pipeline after apply.
