# ALB and target group for backend API
resource "aws_lb" "backend" {
  name               = "${local.project_name}-backend-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = [for s in aws_subnet.public : s.id]

  tags = {
    Name = "${local.project_name}-backend-alb"
  }
}

resource "aws_lb_target_group" "backend" {
  name     = "${local.project_name}-backend-tg"
  port     = var.backend_port
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id

  health_check {
    enabled             = true
    path                = "/health"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    interval            = 30
    timeout             = 5
  }

  tags = {
    Name = "${local.project_name}-backend-tg"
  }
}

resource "aws_lb_target_group_attachment" "backend" {
  target_group_arn = aws_lb_target_group.backend.arn
  target_id        = aws_instance.backend.id
  port             = var.backend_port
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.backend.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend.arn
  }
}

# Optional: Route 53 record for API (set route53_zone_id to enable)
variable "route53_zone_id" {
  description = "Route 53 hosted zone ID for API record (leave empty to skip DNS)"
  type        = string
  default     = ""
}

variable "api_domain_name" {
  description = "Domain name for the backend API (e.g. api.dalla.example.com)"
  type        = string
  default     = ""
}

resource "aws_route53_record" "api" {
  count   = var.route53_zone_id != "" && var.api_domain_name != "" ? 1 : 0
  zone_id = var.route53_zone_id
  name    = var.api_domain_name
  type    = "A"

  alias {
    name                   = aws_lb.backend.dns_name
    zone_id                = aws_lb.backend.zone_id
    evaluate_target_health = true
  }
}

output "alb_dns_name" {
  description = "DNS name of the backend ALB"
  value       = aws_lb.backend.dns_name
}

output "api_url" {
  description = "URL to reach the backend API (ALB DNS or Route 53 if set)"
  value       = var.route53_zone_id != "" && var.api_domain_name != "" ? "http://${var.api_domain_name}" : "http://${aws_lb.backend.dns_name}"
}
