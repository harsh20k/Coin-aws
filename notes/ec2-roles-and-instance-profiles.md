## EC2 Roles, Instance Profiles, and SSM

- **Instance role (IAM role)**: Defines **what the EC2 instance is allowed to do** in AWS. It has:
  - A **permissions policy** (e.g. `ssm:GetParameter`, `bedrock:InvokeModel`, ECR read, etc.).
  - A **trust policy** that allows the **EC2 service** (`ec2.amazonaws.com`) to assume it.

- **Instance profile**: An EC2‑specific container that holds **exactly one IAM role** and is what you actually **attach to an EC2 instance**.
  - EC2 doesn’t attach roles directly; it only knows about **instance profiles**.
  - When the instance launches with an instance profile, EC2 assumes the role and exposes **temporary credentials via IMDS** (Instance Metadata Service).

- **How this project uses it**:
  - Terraform defines an **EC2 backend role** with least‑privilege permissions:
    - Read SSM parameters (e.g. `DATABASE_URL`, Cognito config).
    - Read from ECR to pull the backend image.
    - Use SSM Managed Instance Core (for Run Command).
    - Invoke Bedrock models for chat.
  - Terraform then wraps that role in an **`aws_iam_instance_profile`** and attaches it to the backend EC2 instance (`iam_instance_profile` argument).
  - The backend instance gets **short‑lived AWS credentials** automatically through IMDS; no long‑term access keys are stored on the instance.

- **RDS credentials flow**:
  - Terraform generates a **random RDS password** and builds a `DATABASE_URL` in `rds.tf`.
  - That `DATABASE_URL` is stored as a **SecureString SSM parameter** in `ssm.tf`.
  - The EC2 instance role gives the instance **permission to read that SSM parameter**.
  - Deploy scripts / the app read `DATABASE_URL` (from SSM → env/config), and SQLAlchemy uses it to connect to RDS.

- **Key takeaway**:  
  - **Role** = “what can this identity do?”  
  - **Instance profile** = “how do we attach that role to this EC2 instance so it gets temporary credentials?”  
  - **SSM** holds the secrets (like DB URL); the **EC2 role + instance profile** provide the secure way for the instance to fetch them without long‑lived keys.

