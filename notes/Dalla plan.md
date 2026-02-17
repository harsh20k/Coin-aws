# Dalla Project.

```ad-info
A smart finance advisor web-app where users log their transactions and get personalised advice and ask questions about their budget and habits.
```

## Simple day‑by‑day checklist (Feb 12–23)

### [[Feb 12]] 
- **Main 1**: Write 3–5 sentences describing what the app will do for a normal user.
- **Main 2**: Roughly draw the app flow: user → website → server → database → AI advice.
- **Nice**: Decide tech: React or simple HTML/JS; choose one and stick to it.

### [[Feb 13]]
- **Main 1**: Decide what a “transaction” looks like (fields like amount, date, category, note).
- **Main 2**: List the screens/pages you will have (add transaction, list, insights).
- **Nice**: List the buttons/actions you need on each screen.

### [[Feb 17]]
- **Main 1**: Add Dockerfiles for backend and frontend so the app can run in containers.
- **Main 2**: Add Docker Compose to run db, backend, and frontend locally with one command.
- **Nice**: Note the run commands in Deploy-local.md or README.

### Feb 16
- **Main 1**: Add Terraform for deploy foundation: VPC (if needed), RDS (Postgres), and ECR repos for backend and frontend images.
- **Main 2**: Get Docker images building and pushed to ECR (or at least build and run via Docker Compose locally).
- **Nice**: Document the deploy and run commands in a note or README.

### Feb 17
- **Main 1**: Add ECS cluster, task definitions for backend and frontend, and ALB with target groups.
- **Main 2**: Run the containerized app on ECS (Fargate); backend talks to RDS, frontend to backend.
- **Nice**: Add health checks and confirm the app is reachable via the ALB URL.

### Feb 18
- **Main 1**: Wire CI/CD: CodeCommit (or source repo), CodeBuild (build and test), CodePipeline (trigger on push).
- **Main 2**: Achieve a single-command or push-based deploy (pipeline builds images, updates ECS services).
- **Nice**: Store env and secrets (e.g. `DATABASE_URL`, Cognito) via Terraform/Secrets Manager for the pipeline and ECS.

### Feb 19
- **Main 1**: Wire the Chat page to AWS Bedrock (or chosen AI service); call from the backend with user context.
- **Main 2**: Scope AI answers to the user’s wallets, transactions, budgets, and goals (send summary or structured context in the prompt).
- **Nice**: Try one or two prompt variants and pick the one that works best.

### Feb 20
- **Main 1**: Ensure create/edit/delete for wallets and transactions work end-to-end in the UI and backend.
- **Main 2**: Same for budgets and goals (and subcategories where applicable).
- **Nice**: Fix any broken or missing flows you find along the way.

### Feb 21
- **Main 1**: Seed default subcategories per transaction type; allow user-defined subcategories in the backend and UI.
- **Main 2**: Expose subcategory management in the core flows (e.g. when adding/editing transactions).
- **Nice**: Polish the Chat UI (loading state, error messages, layout).

### Feb 22
- **Main 1**: Confirm project requirements: at least one service each from Compute, Storage, Networking, Database; IaC; runs within AWS Academy constraints.
- **Main 2**: Fix any remaining bugs in the main flows and ensure the deployed app is stable.
- **Nice**: UI polish: labels, spacing, simple colors so the app looks presentable.

### Feb 23
- **Main 1**: Write a simple report outline: intro, what you built, which AWS services, how AI is used.
- **Main 2**: Draw a neat architecture diagram (e.g. diagrams.net) and export it.
- **Nice**: Draft bullet points for what you will say in the video demo; take screenshots for the report.

### Feb 23
- **Main 1**: Do a full dry run: pretend you are recording the video and click through the app.
- **Main 2**: Fix any last-minute issues that break the demo, then stop changing code.
- **Nice**: Double-check you can redeploy everything with one or two simple commands.

