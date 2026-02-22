## ALB removed (Feb 20)

**Change:** ALB (and target group, listener, ALB security group) removed from Terraform. Backend is now reached directly via EC2 Elastic IP.

**Updates**
- **Deleted:** `infra/terraform/alb.tf` (ALB, target group, listener, attachment; Route53 alias record that pointed at ALB).
- **ec2.tf:** Added `aws_eip.backend`, `aws_eip_association.backend`; optional `aws_route53_record.api` (A record to EIP when `route53_zone_id` and `api_domain_name` are set). Outputs: `api_url`, `backend_public_ip`.
- **networking.tf:** Removed ALB security group. Backend SG now allows HTTP from `0.0.0.0/0` on `backend_port` (and SSH unchanged).
- **variables.tf:** Added `route53_zone_id`, `api_domain_name` (default `""`).
- **outputs.tf:** Removed `alb_security_group_id`.
- **frontend.tf:** `frontend_api_url_placeholder` now uses EIP (or Route53 URL when set).
- **monitoring.tf:** Removed `alb_5xx` alarm.

**API URL:** Use `terraform output api_url` → `http://<eip>:8000` (or `http://<api_domain_name>` if Route53 configured). After apply: `terraform apply` then hit that URL for `/health`.

---

## Mixed content: Wallets / API “Load failed” (Feb 20)

**Symptom:** After signup/login on the CloudFront frontend, Wallets (and `/users/me`, transactions) show “Load failed”. Browser console: “requested insecure content from http://…:8000 … This content was blocked and must be served over HTTPS”.

**Root cause:** Frontend is served over **HTTPS** (CloudFront). The app calls the backend over **HTTP** (`VITE_API_URL=http://<eip>:8000`). Browsers block HTTPS pages from loading HTTP resources (mixed content).

**Workaround applied:** In `frontend.tf`, set `viewer_protocol_policy = "allow-all"` so CloudFront does not redirect HTTP → HTTPS. Users open the app via **http://**&lt;cloudfront-domain&gt; (not https). Same-origin HTTP page + HTTP API → no mixed-content block. After change: `terraform apply`.

**Proper fix (for later):** Serve the API over HTTPS (e.g. ALB HTTPS + ACM cert, or proxy `/api/*` through CloudFront to backend) and keep `redirect-to-https` for the frontend.

**Result:** Solution confirmed working. After `terraform apply`, open the app at **http://**&lt;cloudfront-domain&gt; (e.g. `terraform output cloudfront_url` then change `https` to `http`). Signup, login, Wallets, and API calls work.

---

## RDS MasterUserPassword invalid characters (Feb 20)

**Symptom:** `terraform apply` fails creating RDS with: `InvalidParameterValue: The parameter MasterUserPassword is not a valid password. Only printable ASCII characters besides '/', '@', '"', ' ' may be used.`

**Root cause:** Terraform `random_password` with `special = true` uses a default set that can include `@`, `/`, `"`, or space. RDS disallows those in the master password.

**Fix (applied in `infra/terraform/rds.tf`):** Set `override_special` on `random_password` so only RDS-allowed specials are used, e.g. `override_special = "!#$%&*()-_=+[]{}<>:?"` (no `/`, `@`, `"`, or space). After changing this, if the DB instance was partially created, destroy and re-apply so the new password is used.

![[Pasted image 20260220231514.png]]