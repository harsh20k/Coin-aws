terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = ">= 3.5"
    }
    null = {
      source  = "hashicorp/null"
      version = ">= 3.0"
    }
  }

  required_version = ">= 1.5.0"
}

provider "aws" {
  region  = var.aws_region
  profile = var.aws_profile != "" ? var.aws_profile : null
}

locals {
  project_name = var.project_name
}

data "aws_iam_policy_document" "lambda_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "auto_confirm_lambda" {
  name               = "${local.project_name}-auto-confirm-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

resource "aws_iam_role_policy_attachment" "auto_confirm_lambda_basic" {
  role       = aws_iam_role.auto_confirm_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_lambda_function" "auto_confirm" {
  function_name    = "${local.project_name}-auto-confirm"
  filename         = "${path.module}/lambda/auto_confirm.zip"
  source_code_hash = filebase64sha256("${path.module}/lambda/auto_confirm.zip")
  handler          = "index.handler"
  runtime          = "python3.12"
  role             = aws_iam_role.auto_confirm_lambda.arn
}

resource "aws_cognito_user_pool" "main" {
  name = "${local.project_name}-pool"

  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]

  password_policy {
    minimum_length = 8
  }

  schema {
    name                = "email"
    attribute_data_type = "String"
    required            = true
  }

  lambda_config {
    pre_sign_up = aws_lambda_function.auto_confirm.arn
  }
}

resource "aws_lambda_permission" "cognito_pre_signup" {
  statement_id  = "AllowCognitoInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.auto_confirm.function_name
  principal     = "cognito-idp.amazonaws.com"
  source_arn    = aws_cognito_user_pool.main.arn
}

resource "aws_cognito_user_pool_client" "app" {
  name         = "${local.project_name}-app"
  user_pool_id = aws_cognito_user_pool.main.id

  generate_secret     = false
  explicit_auth_flows = ["ALLOW_USER_PASSWORD_AUTH", "ALLOW_REFRESH_TOKEN_AUTH", "ALLOW_USER_SRP_AUTH"]
}

output "user_pool_id" {
  value = aws_cognito_user_pool.main.id
}

output "client_id" {
  value = aws_cognito_user_pool_client.app.id
}
