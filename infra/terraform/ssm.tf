# SSM Parameter Store entries for backend config (EC2 user_data reads these)
resource "aws_ssm_parameter" "database_url" {
  name        = var.ssm_database_url_parameter_name
  description = "DATABASE_URL for Dalla backend"
  type        = "SecureString"
  value       = local.database_url

  tags = {
    Name = "${local.project_name}-database-url"
  }
}

resource "aws_ssm_parameter" "cognito_region" {
  name        = var.ssm_cognito_region_parameter_name
  description = "Cognito region"
  type        = "String"
  value       = var.aws_region

  tags = {
    Name = "${local.project_name}-cognito-region"
  }
}

resource "aws_ssm_parameter" "cognito_user_pool_id" {
  name        = var.ssm_cognito_user_pool_id_parameter_name
  description = "Cognito User Pool ID"
  type        = "String"
  value       = aws_cognito_user_pool.main.id

  tags = {
    Name = "${local.project_name}-cognito-user-pool-id"
  }
}

resource "aws_ssm_parameter" "cognito_app_client_id" {
  name        = var.ssm_cognito_app_client_id_parameter_name
  description = "Cognito App Client ID"
  type        = "String"
  value       = aws_cognito_user_pool_client.app.id

  tags = {
    Name = "${local.project_name}-cognito-app-client-id"
  }
}
