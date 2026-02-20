# CloudWatch log group for backend (EC2 can send uvicorn logs here)
resource "aws_cloudwatch_log_group" "backend" {
  name              = "/${local.project_name}/backend"
  retention_in_days = 14

  tags = {
    Name = "${local.project_name}-backend-logs"
  }
}

# Alarms: EC2 CPU, RDS connections
resource "aws_cloudwatch_metric_alarm" "backend_cpu" {
  alarm_name          = "${local.project_name}-backend-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods   = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 300
  statistic           = "Average"
  threshold           = 80

  dimensions = {
    InstanceId = aws_instance.backend.id
  }

  tags = {
    Name = "${local.project_name}-backend-cpu-alarm"
  }
}

resource "aws_cloudwatch_metric_alarm" "rds_cpu" {
  alarm_name          = "${local.project_name}-rds-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods   = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 80

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.id
  }

  tags = {
    Name = "${local.project_name}-rds-cpu-alarm"
  }
}

output "backend_log_group_name" {
  description = "CloudWatch log group for backend logs"
  value       = aws_cloudwatch_log_group.backend.name
}
