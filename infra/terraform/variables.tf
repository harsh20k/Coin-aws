variable "aws_region" {
  description = "AWS region to deploy resources into"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name used as a prefix for resource naming"
  type        = string
  default     = "dalla"
}

variable "vpc_cidr" {
  description = "CIDR block for the main VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "backend_port" {
  description = "Port on which the backend service listens"
  type        = number
  default     = 8000
}

variable "ssh_ingress_cidr" {
  description = "CIDR allowed to SSH into EC2 instances (use your IP in production)"
  type        = string
  default     = "0.0.0.0/0"
}

