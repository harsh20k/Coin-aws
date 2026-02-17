resource "random_password" "db_password" {
  length  = 24
  special = true
}

resource "aws_db_subnet_group" "main" {
  name       = "${local.project_name}-db-subnets"
  subnet_ids = [for s in aws_subnet.public : s.id]

  tags = {
    Name = "${local.project_name}-db-subnets"
  }
}

resource "aws_db_instance" "main" {
  identifier_prefix   = "${local.project_name}-db-"
  engine              = "postgres"
  engine_version      = "16"
  instance_class      = "db.t3.micro"
  allocated_storage   = 20
  max_allocated_storage = 100

  db_name  = "dalla"
  username = "dalla"
  password = random_password.db_password.result

  port                    = 5432
  db_subnet_group_name    = aws_db_subnet_group.main.name
  vpc_security_group_ids  = [aws_security_group.rds.id]
  publicly_accessible     = false
  skip_final_snapshot     = true
  deletion_protection     = false

  tags = {
    Name = "${local.project_name}-db"
  }
}

locals {
  database_url = "postgresql+asyncpg://dalla:${random_password.db_password.result}@${aws_db_instance.main.address}:${aws_db_instance.main.port}/dalla"
}

output "database_endpoint" {
  description = "Hostname of the RDS instance"
  value       = aws_db_instance.main.address
}

output "database_url" {
  description = "SQLAlchemy-style DATABASE_URL for the backend"
  value       = local.database_url
  sensitive   = true
}

