# Amplify Hosting vs S3 + CloudFront

## What Amplify Hosting does

Amplify Hosting bundles S3, CloudFront, and CI/CD into a single managed product. For a React SPA like coinBaby's frontend:

- Connect a GitHub repo → Amplify builds the app, uploads to S3, puts CloudFront in front, and sets up a deployment pipeline automatically.
- HTTPS and a subdomain (e.g. `main.d1abc.amplifyapp.com`) are configured out of the box.
- On every `git push`, it rebuilds and redeploys — no CodePipeline, no CodeBuild, no S3 sync commands needed.
- Custom domains work through the Amplify console without touching Route 53 manually.

## Why it would work for coinBaby

The frontend is a React SPA with static assets — exactly the use case Amplify is designed for. No server-side rendering, no special routing logic. Amplify would have handled the entire frontend deployment in a few clicks.

## Why we didn't use it

Amplify hides too much. The point of this project is to understand how the pieces fit together:

- **S3** — stores the static build output
- **CloudFront** — CDN, HTTPS, edge caching, SPA routing
- **Route 53** — DNS, alias records
- **ACM** — TLS certificate
- **OAI** — keeps S3 private, only CloudFront can read it

Amplify abstracts all of that behind one service. You get a working deployment but don't learn what's actually happening underneath.
