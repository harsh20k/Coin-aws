# S3 bucket for frontend static assets (CloudFront origin)
variable "frontend_bucket_name" {
  description = "Name of the S3 bucket for frontend assets (must be globally unique)"
  type        = string
  default     = ""
}

locals {
  frontend_bucket_name = var.frontend_bucket_name != "" ? var.frontend_bucket_name : "${local.project_name}-frontend-${data.aws_caller_identity.current.account_id}"
}

data "aws_caller_identity" "current" {}

resource "aws_s3_bucket" "frontend" {
  bucket = local.frontend_bucket_name

  tags = {
    Name = "${local.project_name}-frontend"
  }
}

resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets  = true
}

resource "aws_s3_bucket_versioning" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  versioning_configuration {
    status = "Enabled"
  }
}

# CloudFront origin access identity so CloudFront can read from S3
resource "aws_cloudfront_origin_access_identity" "frontend" {
  comment = "OAI for ${local.project_name} frontend"
}

resource "aws_s3_bucket_policy" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowCloudFrontOnly"
        Effect    = "Allow"
        Principal = { AWS = aws_cloudfront_origin_access_identity.frontend.iam_arn }
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.frontend.arn}/*"
      }
    ]
  })

  depends_on = [aws_s3_bucket_public_access_block.frontend]
}

# CloudFront distribution
resource "aws_cloudfront_distribution" "frontend" {
  enabled             = true
  is_ipv6_enabled      = true
  default_root_object  = "index.html"
  comment              = "${local.project_name} frontend"
  price_class          = "PriceClass_100"

  origin {
    domain_name = aws_s3_bucket.frontend.bucket_regional_domain_name
    origin_id   = "S3-${aws_s3_bucket.frontend.id}"

    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.frontend.cloudfront_access_identity_path
    }
  }

  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "S3-${aws_s3_bucket.frontend.id}"
    viewer_protocol_policy = "allow-all"
    compress               = true

    min_ttl     = 0
    default_ttl = 3600
    max_ttl     = 86400

    forwarded_values {
      query_string = false
      cookies { forward = "none" }
    }
  }

  # SPA: return index.html for 403/404 so client-side routing works
  custom_error_response {
    error_code         = 403
    response_code      = 200
    response_page_path = "/index.html"
  }
  custom_error_response {
    error_code         = 404
    response_code      = 200
    response_page_path = "/index.html"
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = {
    Name = "${local.project_name}-frontend"
  }
}

output "frontend_bucket_name" {
  description = "S3 bucket name for frontend uploads"
  value       = aws_s3_bucket.frontend.id
}

output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name"
  value       = aws_cloudfront_distribution.frontend.domain_name
}

output "cloudfront_url" {
  description = "URL to reach the frontend via CloudFront"
  value       = "https://${aws_cloudfront_distribution.frontend.domain_name}"
}

output "frontend_api_url_placeholder" {
  description = "Set VITE_API_URL to this (or api_url output) when building the frontend"
  value       = var.route53_zone_id != "" && var.api_domain_name != "" ? "http://${var.api_domain_name}" : "http://${aws_eip.backend.public_ip}:${var.backend_port}"
}
