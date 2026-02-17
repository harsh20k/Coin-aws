# ECR repository for backend Docker image
resource "aws_ecr_repository" "backend" {
  name                 = "${local.project_name}-backend"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = "${local.project_name}-backend"
  }
}

output "backend_ecr_repository_url" {
  description = "ECR repository URL for pushing the backend image"
  value       = aws_ecr_repository.backend.repository_url
}
