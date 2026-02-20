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
