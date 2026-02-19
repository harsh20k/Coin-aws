# Copy to terraform.tfvars and fill in. Never commit terraform.tfvars.

aws_region   = "us-east-1"
project_name = "dalla"

# Required: EC2 key pair name (create in AWS first)
ec2_key_name = "dalla-deploy"

# Required: Backend image URI after pushing to ECR (e.g. 123456789.dkr.ecr.us-east-1.amazonaws.com/dalla-backend:latest)
backend_image_uri = "411960113601.dkr.ecr.us-east-1.amazonaws.com/dalla-backend:latest"

# Optional: Restrict SSH to your IP
# ssh_ingress_cidr = "1.2.3.4/32"

# Optional: Route 53 API record
# route53_zone_id   = "Z0123456789ABCDEF"
# api_domain_name  = "api.dalla.example.com"

# Optional: Custom frontend bucket name (must be globally unique)
# frontend_bucket_name = "my-dalla-frontend"
