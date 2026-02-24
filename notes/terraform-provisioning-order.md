# Terraform Provisioning Order

Terraform resolves the dependency graph automatically. This is the logical order resources are created based on their `depends_on` / reference dependencies.

- Phase 1–2: Data lookups + independent foundations (VPC, ECR, IAM roles, EIP, random password)

- Phase 3–4: VPC children (subnets, SGs, route tables) + IAM policy attachments

- Phase 5: Lambda + Cognito (Lambda must exist before the User Pool trigger can reference it)

- Phase 6: RDS (needs subnets + SG + password)

- Phase 7: EC2 (needs AMI, subnet, SG, instance profile) → EIP association

- Phase 8–9: S3 buckets → CloudFront OAI → S3 bucket policy → CloudFront distribution

- Phase 10: SSM parameters (all depend on the values they store — RDS address, Cognito IDs, EIP)

- Phase 11–12: CodeBuild projects → CodePipeline (last, since it references almost everything)

- Phase 13: CloudWatch alarms

- Phase 14: null_resource destroy-time bucket emptier

---

## Phase 1 — Data lookups (no AWS resources created)

These run first since nothing depends on them being created.

1. `data.aws_availability_zones.available` — fetch available AZs in region
2. `data.aws_caller_identity.current` — fetch AWS account ID (used in /bucket names, ARNs)
3. `data.aws_ami.ubuntu` — find latest Ubuntu 20.04 AMI (Canonical)
4. `data.aws_iam_policy_document.*` — all IAM policy documents (in-memory, no API calls that create resources)

---

## Phase 2 — Foundation (no inter-resource dependencies)

Resources with no dependencies on other resources in this config.

5. `aws_vpc.main` — VPC (`10.0.0.0/16`)
6. `aws_ecr_repository.backend` — ECR repo for backend Docker images
7. `random_password.db_password` — generates RDS password
8. `aws_iam_role.auto_confirm_lambda` — IAM role for Pre Sign-Up Lambda
9. `aws_iam_role.backend` — IAM role for EC2 instance
10. `aws_iam_role.codebuild` — IAM role for all CodeBuild projects
11. `aws_iam_role.codepipeline` — IAM role for CodePipeline
12. `aws_codecommit_repository.main` — CodeCommit repo (source of truth for pipeline)
13. `aws_eip.backend` — Elastic IP (allocated before instance exists)
14. `aws_cloudwatch_log_group.backend` — CloudWatch log group for backend

---

## Phase 3 — VPC children

Depend on `aws_vpc.main`.

15. `aws_internet_gateway.igw` — attaches to VPC
16. `aws_subnet.public[0]`, `aws_subnet.public[1]` — 2 public subnets in different AZs
17. `aws_security_group.backend` — backend SG (port 8000 + SSH)
18. `aws_security_group.rds` — RDS SG (port 5432 from backend SG; depends on backend SG)

---

## Phase 4 — Routing + IAM attachments

19. `aws_route_table.public` — depends on VPC + IGW
20. `aws_route_table_association.public[0/1]` — associates subnets with route table
21. `aws_iam_role_policy_attachment.auto_confirm_lambda_basic` — attaches `AWSLambdaBasicExecutionRole` to Lambda role
22. `aws_iam_policy.backend_ssm_access` — inline SSM policy for EC2 role
23. `aws_iam_policy.backend_bedrock_access` — inline Bedrock policy for EC2 role
24. `aws_iam_role_policy_attachment.backend_ssm_access` — attaches SSM policy to EC2 role
25. `aws_iam_role_policy_attachment.backend_ecr_read` — attaches ECR read-only to EC2 role
26. `aws_iam_role_policy_attachment.backend_ssm_managed_core` — attaches `AmazonSSMManagedInstanceCore` to EC2 role
27. `aws_iam_role_policy_attachment.backend_bedrock_access` — attaches Bedrock policy to EC2 role

---

## Phase 5 — Lambda + Cognito

28. `aws_lambda_function.auto_confirm` — Pre Sign-Up Lambda (depends on Lambda IAM role + `auto_confirm.zip`)
29. `aws_cognito_user_pool.main` — Cognito User Pool (depends on Lambda ARN for trigger)
30. `aws_lambda_permission.cognito_pre_signup` — allows Cognito to invoke Lambda (depends on both)
31. `aws_cognito_user_pool_client.app` — app client for the user pool

---

## Phase 6 — RDS subnet group + instance

32. `aws_db_subnet_group.main` — depends on public subnets
33. `aws_db_instance.main` — depends on subnet group, RDS SG, and `random_password`

---

## Phase 7 — EC2 + EIP association

34. `aws_iam_instance_profile.backend` — wraps EC2 IAM role into an instance profile
35. `aws_instance.backend` — depends on: Ubuntu AMI, public subnet[0], backend SG, instance profile
36. `aws_eip_association.backend` — associates EIP with EC2 instance
37. `aws_route53_record.api` *(conditional)* — A record pointing domain to EIP (only if `route53_zone_id` + `api_domain_name` set)

---

## Phase 8 — S3 buckets

38. `aws_s3_bucket.frontend` — frontend static asset bucket
39. `aws_s3_bucket.pipeline_artifacts` — artifact store for CodePipeline
40. `aws_s3_bucket_versioning.frontend` — enables versioning on frontend bucket
41. `aws_s3_bucket_versioning.pipeline_artifacts` — enables versioning on artifacts bucket
42. `aws_s3_bucket_server_side_encryption_configuration.pipeline_artifacts` — AES256 encryption on artifacts bucket
43. `aws_s3_bucket_public_access_block.frontend` — blocks all public access to frontend bucket

---

## Phase 9 — CloudFront + S3 policy

44. `aws_cloudfront_origin_access_identity.frontend` — OAI so CloudFront can read S3
45. `aws_s3_bucket_policy.frontend` — grants OAI read access; depends on public access block + OAI
46. `aws_cloudfront_distribution.frontend` — depends on S3 bucket + OAI

---

## Phase 10 — SSM Parameter Store

All depend on the resources whose values they store.

47. `aws_ssm_parameter.database_url` — SecureString; depends on RDS instance address + password
48. `aws_ssm_parameter.cognito_region` — String; depends on `var.aws_region`
49. `aws_ssm_parameter.cognito_user_pool_id` — String; depends on Cognito User Pool
50. `aws_ssm_parameter.cognito_app_client_id` — String; depends on Cognito App Client
51. `aws_ssm_parameter.api_url` (in `ec2.tf`) — String; depends on EIP (or Route 53 record)

---

## Phase 11 — CodeBuild projects

All depend on: CodeBuild IAM role, ECR repo, EC2 instance, S3 buckets, CloudFront distribution.

52. `aws_codebuild_project.backend_build` — builds Docker image, pushes to ECR
53. `aws_codebuild_project.backend_deploy` — sends SSM Run Command to EC2
54. `aws_codebuild_project.frontend_build` — builds Vite app, syncs to S3, invalidates CloudFront

---

## Phase 12 — CodePipeline

55. `aws_iam_role_policy.codepipeline` — inline policy on CodePipeline role (depends on S3 artifacts bucket + CodeCommit repo)
56. `aws_iam_role_policy.codebuild` — inline policy on CodeBuild role (depends on ECR, S3, EC2, CloudFront)
57. `aws_codepipeline.main` — depends on all three CodeBuild projects, CodeCommit repo, artifacts S3 bucket, CodePipeline role

---

## Phase 13 — CloudWatch alarms

58. `aws_cloudwatch_metric_alarm.backend_cpu` — depends on EC2 instance
59. `aws_cloudwatch_metric_alarm.rds_cpu` — depends on RDS instance

---

## Phase 14 — Destroy-time only

60. `null_resource.empty_frontend_bucket` — runs a local-exec script on `terraform destroy` to empty the versioned S3 bucket before deletion; depends on bucket versioning + bucket policy

---

## Summary by dependency chain

```
VPC
 └─ Subnets → Route Table → Route Table Associations
 └─ Security Groups (backend → rds)
      └─ RDS Subnet Group → RDS Instance → SSM DATABASE_URL
      └─ EC2 IAM Role → Instance Profile → EC2 Instance → EIP Association
                                                        └─ SSM API_URL
                                                        └─ CloudWatch CPU Alarm
Lambda IAM Role → Lambda → Cognito User Pool → Cognito App Client
                                             └─ SSM Cognito params
ECR Repo
S3 (frontend) → CloudFront OAI → S3 Bucket Policy → CloudFront Distribution
S3 (artifacts) → CodePipeline
CodeBuild IAM Role → CodeBuild Projects (x3)
CodeCommit Repo ──┐
CodeBuild Projects ┤→ CodePipeline
S3 Artifacts ──────┘
```
