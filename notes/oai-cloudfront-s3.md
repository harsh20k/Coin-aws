# CloudFront Origin Access Identity (OAI) in coinBaby

## What an OAI is

An **Origin Access Identity (OAI)** is a special CloudFront IAM principal that CloudFront uses when reading from a private S3 bucket. Instead of making the bucket public, you grant read access only to the OAI.

Effectively: **users talk to CloudFront, CloudFront talks to S3 on their behalf**.

## How we use it

In `infra/terraform/frontend.tf`:

- `aws_cloudfront_origin_access_identity.frontend` creates the OAI.
- The S3 bucket policy allows `s3:GetObject` only for `aws_cloudfront_origin_access_identity.frontend.iam_arn`.
- The CloudFront distribution’s `s3_origin_config.origin_access_identity` is set to the OAI path.

This means:

- The frontend S3 bucket is **fully private** (no public access).
- Only our CloudFront distribution can read the React build files.
- Users can never bypass CloudFront and hit S3 directly.

## OAC (Origin Access Control) — AWS’s recommended approach

**Origin Access Control (OAC)** is the newer, recommended way to secure CloudFront → S3. AWS recommends using OAC for new setups and migrating from OAI to OAC.

**Why OAC over OAI:**

- **SigV4 signing** — Uses AWS Signature Version 4; OAI uses legacy signing.
- **SSE-KMS** — OAC can send KMS decryption headers; OAI cannot.
- **All regions** — Works in every S3 region (including opt-in regions after Dec 2022).
- **PUT/DELETE** — Supports dynamic uploads/updates through CloudFront, not just GET/HEAD.
- **IAM** — Works with normal IAM conditions (e.g. `aws:SourceVpc`) instead of OAI’s `CanonicalUser`-style principal.
- **Credentials** — Short-lived credentials with better rotation and less “confused deputy” risk.

**When to use:** Prefer OAC for new distributions, SSE-KMS content, multi-region S3, or any upload/update flow via CloudFront. For existing OAI setups, plan a migration to OAC.

