# Provisioning Cognito User Pool (Terraform)

Easiest way to create a Cognito User Pool and App Client so you can set `VITE_COGNITO_USER_POOL_ID` and `VITE_COGNITO_APP_CLIENT_ID` in the frontend (and matching vars in the backend).

## 1. Terraform file

Create a directory for this (e.g. `terraform/` or `infra/cognito/`) and add `main.tf`:

```hcl
terraform {
  required_providers {
    aws = { source = "hashicorp/aws" }
  }
}

provider "aws" {
  region = "us-east-1"  # or var.region
}

resource "aws_cognito_user_pool" "main" {
  name = "dalla-pool"

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
  name         = "dalla-app"
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
```

## 2. Apply and get IDs

```bash
cd /path/to/terraform
terraform init
terraform apply -auto-approve
terraform output
```

- `user_pool_id` → `VITE_COGNITO_USER_POOL_ID` (and backend `COGNITO_USER_POOL_ID`)
- `client_id` → `VITE_COGNITO_APP_CLIENT_ID` (and backend `COGNITO_APP_CLIENT_ID`)
- Use the same region (e.g. `us-east-1`) for `VITE_COGNITO_REGION` / `COGNITO_REGION`.

## 3. Where the IDs come from (without Terraform)

If you prefer the console:

1. **AWS Console** → Amazon Cognito → User Pools → your pool (or create one).
2. **User pool ID** is on the pool overview (e.g. `us-east-1_xxxxxxxxx`).
3. **App integration** (or App clients) → open/create app client → **Client ID** is there.

CLI:

- `aws cognito-idp list-user-pools --max-results 10` → use `Id` for user pool ID.
- `aws cognito-idp list-user-pool-clients --user-pool-id <USER_POOL_ID>` → use `ClientId` for app client ID.
