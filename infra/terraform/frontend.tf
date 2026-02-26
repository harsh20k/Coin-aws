# S3 bucket for frontend static assets (CloudFront origin)
variable "frontend_bucket_name" {
  description = "Name of the S3 bucket for frontend assets (must be globally unique)"
  type        = string
  default     = ""
}

locals {
  frontend_bucket_name          = var.frontend_bucket_name != "" ? var.frontend_bucket_name : "${local.project_name}-frontend-${data.aws_caller_identity.current.account_id}"
  use_custom_frontend_domain    = var.route53_zone_id != "" && var.frontend_domain_name != ""
}

data "aws_caller_identity" "current" {}

resource "aws_s3_bucket" "frontend" {
  bucket = local.frontend_bucket_name

  tags = {
    Name = "${local.project_name}-frontend"
  }
}

# Empty bucket on destroy (S3 cannot delete non-empty versioned buckets)
resource "null_resource" "empty_frontend_bucket" {
  triggers = { bucket = aws_s3_bucket.frontend.id }

  provisioner "local-exec" {
    when    = destroy
    command = <<-EOT
      BUCKET="${self.triggers.bucket}"
      aws s3api list-object-versions --bucket "$BUCKET" --query 'Versions[].{Key:Key,VersionId:VersionId}' --output text | while IFS=$'\t' read -r key vid; do [ -n "$key" ] && aws s3api delete-object --bucket "$BUCKET" --key "$key" --version-id "$vid" 2>/dev/null || true; done
      aws s3api list-object-versions --bucket "$BUCKET" --query 'DeleteMarkers[].{Key:Key,VersionId:VersionId}' --output text | while IFS=$'\t' read -r key vid; do [ -n "$key" ] && aws s3api delete-object --bucket "$BUCKET" --key "$key" --version-id "$vid" 2>/dev/null || true; done
    EOT
  }

  depends_on = [
    aws_s3_bucket_versioning.frontend,
    aws_s3_bucket_policy.frontend,
  ]
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

# ACM certificate for custom frontend domain (CloudFront requires one even for HTTP)
resource "aws_acm_certificate" "frontend" {
  count             = local.use_custom_frontend_domain ? 1 : 0
  domain_name       = var.frontend_domain_name
  validation_method = "DNS"

  lifecycle { create_before_destroy = true }
}

resource "aws_route53_record" "frontend_cert_validation" {
  for_each = local.use_custom_frontend_domain ? {
    for dvo in aws_acm_certificate.frontend[0].domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  } : {}

  zone_id         = var.route53_zone_id
  name            = each.value.name
  type            = each.value.type
  ttl             = 60
  records         = [each.value.record]
  allow_overwrite = true
}

resource "aws_acm_certificate_validation" "frontend" {
  count                   = local.use_custom_frontend_domain ? 1 : 0
  certificate_arn         = aws_acm_certificate.frontend[0].arn
  validation_record_fqdns = [for r in aws_route53_record.frontend_cert_validation : r.fqdn]
}

# Route 53 alias pointing domain to CloudFront
resource "aws_route53_record" "frontend" {
  count   = local.use_custom_frontend_domain ? 1 : 0
  zone_id = var.route53_zone_id
  name    = var.frontend_domain_name
  type    = "A"

  alias {
    name                   = aws_cloudfront_distribution.frontend.domain_name
    zone_id                = aws_cloudfront_distribution.frontend.hosted_zone_id
    evaluate_target_health = false
  }
}

# CloudFront distribution
resource "aws_cloudfront_distribution" "frontend" {
  enabled             = true
  is_ipv6_enabled      = true
  default_root_object  = "index.html"
  comment              = "${local.project_name} frontend"
  price_class          = "PriceClass_100"
  aliases              = local.use_custom_frontend_domain ? [var.frontend_domain_name] : []

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
    cloudfront_default_certificate = local.use_custom_frontend_domain ? false : true
    acm_certificate_arn            = local.use_custom_frontend_domain ? aws_acm_certificate_validation.frontend[0].certificate_arn : null
    ssl_support_method             = local.use_custom_frontend_domain ? "sni-only" : null
    minimum_protocol_version       = local.use_custom_frontend_domain ? "TLSv1.2_2021" : null
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

output "frontend_url" {
  description = "Frontend URL (custom domain if set, otherwise CloudFront)"
  value       = local.use_custom_frontend_domain ? "http://${var.frontend_domain_name}" : "http://${aws_cloudfront_distribution.frontend.domain_name}"
}

output "frontend_api_url_placeholder" {
  description = "Set VITE_API_URL to this (or api_url output) when building the frontend"
  value       = var.route53_zone_id != "" && var.api_domain_name != "" ? "http://${var.api_domain_name}" : "http://${aws_eip.backend.public_ip}:${var.backend_port}"
}
