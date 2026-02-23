# CodeCommit, CodeBuild, and CodePipeline for CI/CD

# ---------------------------------------------------------------------------
# CodeCommit repository (push code here to trigger pipeline)
# ---------------------------------------------------------------------------
resource "aws_codecommit_repository" "main" {
  repository_name = local.project_name
  description     = "Dalla application source"

  tags = {
    Name = "${local.project_name}-repo"
  }
}

output "codecommit_repository_url" {
  description = "CodeCommit clone URL (SSH)"
  value       = aws_codecommit_repository.main.clone_url_ssh
}

output "codecommit_repository_https_url" {
  description = "CodeCommit clone URL (HTTPS)"
  value       = aws_codecommit_repository.main.clone_url_http
}

# ---------------------------------------------------------------------------
# Pipeline artifact store
# ---------------------------------------------------------------------------
resource "aws_s3_bucket" "pipeline_artifacts" {
  bucket = "${local.project_name}-pipeline-artifacts-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name = "${local.project_name}-pipeline-artifacts"
  }
}

resource "aws_s3_bucket_versioning" "pipeline_artifacts" {
  bucket = aws_s3_bucket.pipeline_artifacts.id

  versioning_configuration {
    status = "Enabled"
  }
}

# CodePipeline requires encryption or no encryption; default SSE is fine.
resource "aws_s3_bucket_server_side_encryption_configuration" "pipeline_artifacts" {
  bucket = aws_s3_bucket.pipeline_artifacts.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# ---------------------------------------------------------------------------
# IAM role for CodePipeline
# ---------------------------------------------------------------------------
data "aws_iam_policy_document" "codepipeline_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["codepipeline.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "codepipeline" {
  name               = "${local.project_name}-codepipeline-role"
  assume_role_policy = data.aws_iam_policy_document.codepipeline_assume.json
}

data "aws_iam_policy_document" "codepipeline_permissions" {
  statement {
    sid    = "S3"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:GetBucketLocation"
    ]
    resources = [
      aws_s3_bucket.pipeline_artifacts.arn,
      "${aws_s3_bucket.pipeline_artifacts.arn}/*"
    ]
  }
  statement {
    sid    = "CodeCommit"
    effect = "Allow"
    actions = [
      "codecommit:GetBranch",
      "codecommit:GetCommit",
      "codecommit:GetRepository",
      "codecommit:ListBranches",
      "codecommit:ListRepositories",
      "codecommit:UploadArchive",
      "codecommit:GetUploadArchiveStatus"
    ]
    resources = [aws_codecommit_repository.main.arn]
  }
  statement {
    sid    = "CodeBuild"
    effect = "Allow"
    actions = [
      "codebuild:BatchGetBuilds",
      "codebuild:StartBuild"
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "codepipeline" {
  name   = "${local.project_name}-codepipeline-policy"
  role   = aws_iam_role.codepipeline.id
  policy = data.aws_iam_policy_document.codepipeline_permissions.json
}

# ---------------------------------------------------------------------------
# IAM role for CodeBuild (shared by all three projects)
# ---------------------------------------------------------------------------
data "aws_iam_policy_document" "codebuild_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["codebuild.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "codebuild" {
  name               = "${local.project_name}-codebuild-role"
  assume_role_policy = data.aws_iam_policy_document.codebuild_assume.json
}

data "aws_iam_policy_document" "codebuild_permissions" {
  statement {
    sid    = "Logs"
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]
    resources = ["*"]
  }
  statement {
    sid    = "S3Artifacts"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:GetBucketLocation"
    ]
    resources = [
      aws_s3_bucket.pipeline_artifacts.arn,
      "${aws_s3_bucket.pipeline_artifacts.arn}/*"
    ]
  }
  statement {
    sid    = "ECR"
    effect = "Allow"
    actions = [
      "ecr:GetAuthorizationToken"
    ]
    resources = ["*"]
  }
  statement {
    sid    = "ECRPush"
    effect = "Allow"
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage",
      "ecr:PutImage",
      "ecr:InitiateLayerUpload",
      "ecr:UploadLayerPart",
      "ecr:CompleteLayerUpload"
    ]
    resources = [aws_ecr_repository.backend.arn]
  }
  statement {
    sid    = "SSMSendCommand"
    effect = "Allow"
    actions = [
      "ssm:SendCommand"
    ]
    resources = [
      "arn:aws:ec2:${var.aws_region}:${data.aws_caller_identity.current.account_id}:instance/${aws_instance.backend.id}",
      "arn:aws:ssm:${var.aws_region}::document/AWS-RunShellScript"
    ]
  }
  statement {
    sid    = "SSMGetParameter"
    effect = "Allow"
    actions = [
      "ssm:GetParameter",
      "ssm:GetParameters"
    ]
    resources = [
      "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter/${local.project_name}/prod/*"
    ]
  }
  statement {
    sid    = "S3Frontend"
    effect = "Allow"
    actions = [
      "s3:PutObject",
      "s3:PutObjectAcl",
      "s3:GetObject",
      "s3:ListBucket",
      "s3:DeleteObject"
    ]
    resources = [
      aws_s3_bucket.frontend.arn,
      "${aws_s3_bucket.frontend.arn}/*"
    ]
  }
  statement {
    sid    = "CloudFront"
    effect = "Allow"
    actions = [
      "cloudfront:CreateInvalidation",
      "cloudfront:GetDistribution"
    ]
    resources = [aws_cloudfront_distribution.frontend.arn]
  }
  statement {
    sid    = "EC2Describe"
    effect = "Allow"
    actions = [
      "ec2:DescribeInstances",
      "ec2:DescribeInstanceStatus"
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "codebuild" {
  name   = "${local.project_name}-codebuild-policy"
  role   = aws_iam_role.codebuild.id
  policy = data.aws_iam_policy_document.codebuild_permissions.json
}

# ---------------------------------------------------------------------------
# CodeBuild: backend image build and push to ECR
# ---------------------------------------------------------------------------
resource "aws_codebuild_project" "backend_build" {
  name          = "${local.project_name}-backend-build"
  service_role  = aws_iam_role.codebuild.arn
  build_timeout = 15

  artifacts {
    type = "CODEPIPELINE"
  }

  environment {
    compute_type                = "BUILD_GENERAL1_MEDIUM"
    image                       = "aws/codebuild/standard:7.0"
    type                        = "LINUX_CONTAINER"
    image_pull_credentials_type = "CODEBUILD"

    environment_variable {
      name  = "ECR_REPOSITORY_URI"
      value = aws_ecr_repository.backend.repository_url
    }
    environment_variable {
      name  = "AWS_REGION"
      value = var.aws_region
    }
  }

  source {
    type      = "CODEPIPELINE"
    buildspec = "buildspec-backend.yml"
  }

  logs_config {
    cloudwatch_logs {
      group_name  = "/aws/codebuild/${local.project_name}-backend-build"
      stream_name = "build"
    }
  }
}

# ---------------------------------------------------------------------------
# CodeBuild: deploy backend (SSM Run Command to EC2)
# ---------------------------------------------------------------------------
resource "aws_codebuild_project" "backend_deploy" {
  name          = "${local.project_name}-backend-deploy"
  service_role  = aws_iam_role.codebuild.arn
  build_timeout = 15

  artifacts {
    type = "CODEPIPELINE"
  }

  environment {
    compute_type                = "BUILD_GENERAL1_SMALL"
    image                       = "aws/codebuild/standard:7.0"
    type                        = "LINUX_CONTAINER"
    image_pull_credentials_type = "CODEBUILD"

    environment_variable {
      name  = "BACKEND_INSTANCE_ID"
      value = aws_instance.backend.id
    }
    environment_variable {
      name  = "ECR_REPOSITORY_URI"
      value = "${aws_ecr_repository.backend.repository_url}:latest"
    }
    environment_variable {
      name  = "AWS_REGION"
      value = var.aws_region
    }
    environment_variable {
      name  = "SSM_DATABASE_URL"
      value = var.ssm_database_url_parameter_name
    }
    environment_variable {
      name  = "SSM_COGNITO_REGION"
      value = var.ssm_cognito_region_parameter_name
    }
    environment_variable {
      name  = "SSM_COGNITO_USER_POOL_ID"
      value = var.ssm_cognito_user_pool_id_parameter_name
    }
    environment_variable {
      name  = "SSM_COGNITO_APP_CLIENT_ID"
      value = var.ssm_cognito_app_client_id_parameter_name
    }
    environment_variable {
      name  = "BACKEND_PORT"
      value = tostring(var.backend_port)
    }
  }

  source {
    type      = "CODEPIPELINE"
    buildspec = "buildspec-backend-deploy.yml"
  }

  logs_config {
    cloudwatch_logs {
      group_name  = "/aws/codebuild/${local.project_name}-backend-deploy"
      stream_name = "build"
    }
  }
}

# ---------------------------------------------------------------------------
# CodeBuild: frontend build and deploy to S3 + CloudFront invalidation
# ---------------------------------------------------------------------------
resource "aws_codebuild_project" "frontend_build" {
  name          = "${local.project_name}-frontend-build"
  service_role  = aws_iam_role.codebuild.arn
  build_timeout = 15

  artifacts {
    type = "CODEPIPELINE"
  }

  environment {
    compute_type                = "BUILD_GENERAL1_SMALL"
    image                       = "aws/codebuild/standard:7.0"
    type                        = "LINUX_CONTAINER"
    image_pull_credentials_type = "CODEBUILD"

    environment_variable {
      name  = "FRONTEND_BUCKET"
      value = aws_s3_bucket.frontend.id
    }
    environment_variable {
      name  = "CLOUDFRONT_DISTRIBUTION_ID"
      value = aws_cloudfront_distribution.frontend.id
    }
    environment_variable {
      name  = "AWS_REGION"
      value = var.aws_region
    }
    environment_variable {
      name  = "SSM_API_URL"
      value = var.ssm_api_url_parameter_name
    }
    environment_variable {
      name  = "SSM_COGNITO_REGION"
      value = var.ssm_cognito_region_parameter_name
    }
    environment_variable {
      name  = "SSM_COGNITO_USER_POOL_ID"
      value = var.ssm_cognito_user_pool_id_parameter_name
    }
    environment_variable {
      name  = "SSM_COGNITO_APP_CLIENT_ID"
      value = var.ssm_cognito_app_client_id_parameter_name
    }
  }

  source {
    type      = "CODEPIPELINE"
    buildspec = "buildspec-frontend.yml"
  }

  logs_config {
    cloudwatch_logs {
      group_name  = "/aws/codebuild/${local.project_name}-frontend-build"
      stream_name = "build"
    }
  }
}

# ---------------------------------------------------------------------------
# CodePipeline
# ---------------------------------------------------------------------------
variable "codecommit_branch" {
  description = "CodeCommit branch to trigger the pipeline"
  type        = string
  default     = "main"
}

resource "aws_codepipeline" "main" {
  name     = "${local.project_name}-pipeline"
  role_arn = aws_iam_role.codepipeline.arn

  artifact_store {
    location = aws_s3_bucket.pipeline_artifacts.bucket
    type     = "S3"
  }

  stage {
    name = "Source"

    action {
      name             = "Source"
      category         = "Source"
      owner            = "AWS"
      provider         = "CodeCommit"
      version          = "1"
      output_artifacts = ["SourceOutput"]

      configuration = {
        RepositoryName = aws_codecommit_repository.main.repository_name
        BranchName     = var.codecommit_branch
      }
    }
  }

  stage {
    name = "BuildBackend"

    action {
      name             = "BuildBackend"
      category         = "Build"
      owner            = "AWS"
      provider         = "CodeBuild"
      version          = "1"
      input_artifacts   = ["SourceOutput"]
      output_artifacts = ["BackendBuildOutput"]

      configuration = {
        ProjectName = aws_codebuild_project.backend_build.name
      }
    }
  }

  stage {
    name = "DeployBackend"

    action {
      name             = "DeployBackend"
      category         = "Build"
      owner            = "AWS"
      provider         = "CodeBuild"
      version          = "1"
      input_artifacts   = ["SourceOutput"]

      configuration = {
        ProjectName = aws_codebuild_project.backend_deploy.name
      }
    }
  }

  stage {
    name = "BuildFrontend"

    action {
      name             = "BuildFrontend"
      category         = "Build"
      owner            = "AWS"
      provider         = "CodeBuild"
      version          = "1"
      input_artifacts   = ["SourceOutput"]

      configuration = {
        ProjectName = aws_codebuild_project.frontend_build.name
      }
    }
  }
}
