## AWS deploy – 502 Bad Gateway (Feb 19)

**Symptom:** After `terraform apply` (backend EC2 + ALB + target group attachment created), hitting the ALB URL returns **502 Bad Gateway**.

**Likely causes**

1. **No healthy targets** – ALB has no healthy targets to forward to. Check **EC2 → Target Groups → dalla-backend-tg → Targets**; if status is Unhealthy or Initial, ALB will return 502.
2. **Container not running** – Instance `user_data` installs Docker, fetches SSM params, then `docker run`. If any step fails (e.g. `aws ssm get-parameter` fails due to missing param or IAM, or ECR pull fails), the container never starts. Check **`/var/log/cloud-init-output.log`** on the instance.
3. **App crash after start** – Container runs but app exits (e.g. DB connection failure, missing tables). Check **`docker logs backend`** on the instance and **CloudWatch Logs → /dalla/backend**.
4. **Health check delay** – ALB health check is every 30s with `healthy_threshold = 2`; new instance can take ~1 minute to show Healthy. Wait and retry.
5. **SSM / DB not ready** – If SSM parameters (e.g. `DATABASE_URL`) were missing or wrong when `user_data` ran, script or app can fail. Ensure table-creation script has been run against RDS once (see Deploy-AWS.md).

**Debug steps**

- Target Groups → Targets: note Healthy vs Unhealthy.
- Connect to backend instance (SSH or Session Manager): `sudo docker ps`, `sudo cat /var/log/cloud-init-output.log`, `curl -s http://localhost:8000/health`, `docker logs backend`.
