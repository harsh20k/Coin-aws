output "vpc_id" {
  description = "ID of the main VPC"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = [for s in aws_subnet.public : s.id]
}

output "alb_security_group_id" {
  description = "Security group ID for the ALB"
  value       = aws_security_group.alb.id
}

output "backend_security_group_id" {
  description = "Security group ID for backend instances"
  value       = aws_security_group.backend.id
}

output "rds_security_group_id" {
  description = "Security group ID for RDS"
  value       = aws_security_group.rds.id
}

