# Dalla Notes Index

This folder contains all the written notes for the Dalla / coinBaby project: architecture decisions, deployment steps, AWS service choices, and daily logs. Use this file as the entry point.

---

## High-level project notes

- [Project report](report.md) — final project write-up and rationale for architecture and services.
- [Dalla plan](Dalla%20plan.md) — initial scope, milestones, and planning.
- [Progress log](progress.md) — running log of what was done each day.
- [Open questions](Questions.md) — questions captured while building the project.

---

## Architecture and design

- [Overall architecture](architecture.md) — high-level system design and components.
- [Database schema](schema.md) — ERD-level thinking and how tables relate.
- [Lambda vs EC2 for backend](lambda-vs-ec2-backend.md) — why the backend runs on EC2 instead of Lambda, with a focus on connection pools and stateless design.
- [FastAPI validation vs API Gateway](fastapi-validation-vs-api-gateway.md) — why we did not put API Gateway in front of FastAPI.
- [Amplify Hosting vs S3 + CloudFront](amplify-vs-s3-cloudfront.md) — why we chose explicit S3 + CloudFront instead of Amplify Hosting.
- [Services used](services-used.md) — list of AWS services in the project and what each one does.
- [AWS Lex, Bedrock, and related services](aws-lex-bedrock-and-related-services.md) — notes on conversational AI options on AWS.
- [Chatbot / Bedrock proposal](chatbot-bedrock-proposal.md) — early thinking around using Bedrock for the assistant.

---

## Deployment and infrastructure

- [Deploy locally](Deploy-local.md) — how to run the app on your machine.
- [Deploy to AWS](Deploy-AWS.md) — end-to-end steps to provision and deploy on AWS.
- [Terraform provisioning order](terraform-provisioning-order.md) — recommended order for applying Terraform modules.
- [Provisioning Cognito user pool](provisioning-cognito-userpool.md) — details specific to Cognito setup.

---

## Chronological work logs

Daily notes that capture what happened on specific days while building the project:

- [Feb 12](Feb%2012.md)
- [Feb 13](Feb%2013.md)
- [Feb 17](Feb%2017.md)
- [Feb 19](Feb%2019.md)
- [Feb 20](Feb%2020.md)
- [Feb 22](Feb%2022.md)
- [Feb 23](Feb%2023.md)
- [Feb 24](Feb%2024.md)
- [Feb 25](Feb%2025.md)

These are useful if you want to reconstruct the timeline of decisions or debug when something changed.

