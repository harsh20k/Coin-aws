variable "backend_image_uri" {
  description = "Container image URI for the backend (e.g. ECR URI)"
  type        = string
}

variable "ec2_instance_type" {
  description = "Instance type for the backend EC2 instance"
  type        = string
  default     = "t3.micro"
}

variable "ec2_key_name" {
  description = "Name of an existing EC2 key pair to enable SSH access"
  type        = string
}

variable "ssm_database_url_parameter_name" {
  description = "SSM parameter name that stores the DATABASE_URL"
  type        = string
  default     = "/dalla/prod/DATABASE_URL"
}

variable "ssm_cognito_region_parameter_name" {
  description = "SSM parameter name for Cognito region"
  type        = string
  default     = "/dalla/prod/COGNITO_REGION"
}

variable "ssm_cognito_user_pool_id_parameter_name" {
  description = "SSM parameter name for Cognito User Pool ID"
  type        = string
  default     = "/dalla/prod/COGNITO_USER_POOL_ID"
}

variable "ssm_cognito_app_client_id_parameter_name" {
  description = "SSM parameter name for Cognito App Client ID"
  type        = string
  default     = "/dalla/prod/COGNITO_APP_CLIENT_ID"
}

data "aws_iam_policy_document" "ec2_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "backend" {
  name               = "${local.project_name}-backend-role"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume_role.json
}

data "aws_iam_policy_document" "backend_ssm_access" {
  statement {
    actions = [
      "ssm:GetParameter",
      "ssm:GetParameters",
      "ssm:GetParametersByPath",
      "secretsmanager:GetSecretValue"
    ]

    resources = ["*"]
  }
}

resource "aws_iam_policy" "backend_ssm_access" {
  name   = "${local.project_name}-backend-ssm-access"
  policy = data.aws_iam_policy_document.backend_ssm_access.json
}

resource "aws_iam_role_policy_attachment" "backend_ssm_access" {
  role       = aws_iam_role.backend.name
  policy_arn = aws_iam_policy.backend_ssm_access.arn
}

resource "aws_iam_instance_profile" "backend" {
  name = "${local.project_name}-backend-instance-profile"
  role = aws_iam_role.backend.name
}

resource "aws_eip" "backend" {
  domain = "vpc"
  tags = {
    Name = "${local.project_name}-backend-eip"
  }
}

resource "aws_instance" "backend" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.ec2_instance_type
  subnet_id              = aws_subnet.public[0].id
  vpc_security_group_ids = [aws_security_group.backend.id]
  key_name               = var.ec2_key_name
  iam_instance_profile   = aws_iam_instance_profile.backend.name

  user_data = <<-EOF
              #!/bin/bash
              set -e

              apt-get update -y
              apt-get install -y docker.io awscli
              systemctl enable docker
              systemctl start docker

              REGION="${var.aws_region}"

              DATABASE_URL=$(aws ssm get-parameter --name "${var.ssm_database_url_parameter_name}" --with-decryption --region "$REGION" --query "Parameter.Value" --output text)
              COGNITO_REGION=$(aws ssm get-parameter --name "${var.ssm_cognito_region_parameter_name}" --with-decryption --region "$REGION" --query "Parameter.Value" --output text)
              COGNITO_USER_POOL_ID=$(aws ssm get-parameter --name "${var.ssm_cognito_user_pool_id_parameter_name}" --with-decryption --region "$REGION" --query "Parameter.Value" --output text)
              COGNITO_APP_CLIENT_ID=$(aws ssm get-parameter --name "${var.ssm_cognito_app_client_id_parameter_name}" --with-decryption --region "$REGION" --query "Parameter.Value" --output text)

              docker run -d \
                --name backend \
                -p ${var.backend_port}:${var.backend_port} \
                -e DATABASE_URL="$DATABASE_URL" \
                -e COGNITO_REGION="$COGNITO_REGION" \
                -e COGNITO_USER_POOL_ID="$COGNITO_USER_POOL_ID" \
                -e COGNITO_APP_CLIENT_ID="$COGNITO_APP_CLIENT_ID" \
                ${var.backend_image_uri}
              EOF

  tags = {
    Name = "${local.project_name}-backend-ec2"
  }

  depends_on = [
    aws_ssm_parameter.database_url,
    aws_ssm_parameter.cognito_region,
    aws_ssm_parameter.cognito_user_pool_id,
    aws_ssm_parameter.cognito_app_client_id,
  ]
}

resource "aws_eip_association" "backend" {
  instance_id   = aws_instance.backend.id
  allocation_id = aws_eip.backend.id
}

resource "aws_route53_record" "api" {
  count   = var.route53_zone_id != "" && var.api_domain_name != "" ? 1 : 0
  zone_id = var.route53_zone_id
  name    = var.api_domain_name
  type    = "A"
  ttl     = 300
  records = [aws_eip.backend.public_ip]
}

data "aws_ami" "ubuntu" {
  most_recent = true

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  owners = ["099720109477"] # Canonical
}

output "backend_instance_id" {
  description = "ID of the backend EC2 instance"
  value       = aws_instance.backend.id
}

output "api_url" {
  description = "URL to reach the backend API (EIP or Route 53 if set)"
  value       = var.route53_zone_id != "" && var.api_domain_name != "" ? "http://${var.api_domain_name}" : "http://${aws_eip.backend.public_ip}:${var.backend_port}"
}

output "backend_public_ip" {
  description = "Public IP of the backend EC2 (Elastic IP)"
  value       = aws_eip.backend.public_ip
}

