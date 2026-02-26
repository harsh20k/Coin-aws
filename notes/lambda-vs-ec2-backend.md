# Lambda vs EC2 for a Backend — Connection Pools and Stateless Design

## Why connection pools matter

Opening a database connection is expensive. It involves a TCP handshake, authentication, and setup — every time. An **async connection pool** is a pre-warmed set of those connections that the app keeps open and ready in memory.

Instead of opening a new connection every time a request needs the database, the app borrows one from the pool, uses it, and returns it. SQLAlchemy manages this automatically. "Async" just means it does this without blocking — while one request is waiting for the DB to respond, another request can run on the same thread.

Think of it like a taxi rank. Instead of calling a new taxi every time someone needs a ride, there are always a few taxis waiting. You grab one, use it, it comes back to the rank.

## What "across requests" means

The pool is shared across all HTTP requests — from any user. It lives in the server process's memory.

As long as the FastAPI process is running (a persistent Docker container on EC2), the pool stays alive:

- Request from User A comes in → borrows connection 1 → query runs → connection 1 returns to pool.
- Request from User B comes in a millisecond later → borrows connection 1 again.

The pool is shared across all traffic, not per-user.

## Why Lambda breaks this

Lambda has no persistent process. Each invocation may start a fresh Python process — no pool, no pre-warmed connections. So instead of borrowing from the rank, you're calling a new taxi from scratch every time.

If 50 users hit the app at once, you're opening 50 new DB connections simultaneously. RDS `t3.micro` has a hard limit on concurrent connections (~80–100 for that instance size). You'd hit it fast.

---

## The alternative: stateless Lambda + RDS Proxy

There is a proper way to run Lambda with RDS — **RDS Proxy**.

RDS Proxy sits between Lambda and RDS. It maintains a persistent connection pool *itself*, so Lambda functions don't open raw DB connections. Each Lambda invocation connects to the Proxy (cheap), and the Proxy multiplexes those onto a smaller set of real RDS connections (expensive, but reused).

```
Lambda invocation 1 ──┐
Lambda invocation 2 ──┤──► RDS Proxy (pool) ──► RDS
Lambda invocation 3 ──┘
```

This solves the connection exhaustion problem. But it adds:

- **Cost** — RDS Proxy is billed per vCPU of the RDS instance, on top of the RDS cost.
- **Latency** — one extra hop in every query path.
- **Complexity** — another managed resource to configure, secure (IAM auth), and reason about.

For a project at this scale, that trade-off is not worth it.

---

## The stateless Lambda approach (redesigning the backend)

If you *wanted* to build the backend as pure Lambda from the start, you'd design it differently:

1. **No connection pool.** Each Lambda opens a connection via RDS Proxy (or accepts the cold-start cost), runs the query, and closes. You rely on RDS Proxy to absorb the connection churn.

2. **No startup initialisation.** The `seed_default_subcategories()` call that runs on app startup doesn't work in Lambda — there's no reliable "startup". You'd move that to a one-time migration script or a separate Lambda triggered by a CloudFormation custom resource or EventBridge rule.

3. **Stateless handlers.** Each Lambda function handles one route or one event. No shared in-memory state between invocations. Any state lives in the database or a cache (e.g. ElastiCache).

4. **API Gateway in front.** Lambda functions don't have a public URL by default. You'd put API Gateway in front to route HTTP requests to the right function. This adds another layer — request validation, rate limiting, CORS config — all managed separately from the application code.

The result is a fully serverless backend that scales to zero (no cost when idle) and scales horizontally without any instance management. That's genuinely useful for unpredictable or spiky traffic.

For coinBaby — a project-scale app with a small, predictable user base — the operational overhead of that design outweighs the benefits. EC2 with a persistent FastAPI process is simpler, cheaper, and easier to reason about.

---

## Scaling the database — Aurora Serverless vs RDS

### What Aurora Serverless v2 improves

Standard RDS (`db.t3.micro`) is fixed at 1 vCPU and 1GB RAM. If query load spikes, there's no headroom — queries queue up and slow down. Resizing requires a manual instance change and a reboot.

Aurora Serverless v2 measures how hard the database engine is working (CPU, memory, query throughput) and automatically adjusts its compute capacity in **ACUs (Aurora Capacity Units)** — each ACU is roughly 2GB RAM + proportional CPU. You set a min and max:

```hcl
serverlessv2_scaling_configuration {
  min_capacity = 0.5   # ~1GB RAM
  max_capacity = 16.0  # ~32GB RAM
}
```

As traffic increases, Aurora slides capacity up within seconds. When traffic drops, it slides back down. You're only billed for what you use.

This is what "better auto-scaling on the DB compute side" means — the database engine can process queries faster under load without manual intervention.

### What Aurora does NOT fix — the connection limit

The real bottleneck at high concurrency (e.g. 5,000 users) is **connection count**, not compute.

PostgreSQL has a hard limit on simultaneous connections (`max_connections`), regardless of whether it's RDS or Aurora. At 5,000 concurrent users each holding a connection, you'd exhaust that limit fast — and Aurora does nothing about this. You can have a very powerful DB engine that still refuses new connections because the connection count ceiling is hit.

To actually handle that scale you still need:

- **RDS Proxy** (or PgBouncer) — pools connections so thousands of app-side connections map to a small number of actual DB connections
- **Multiple EC2 instances behind an ALB** — a single `t3.micro` saturates well before 5,000 users
- **Read replicas** — offload read-heavy queries to a replica

Aurora improves the compute headroom. The connection exhaustion problem is a separate layer that requires a connection pooler.

---

## Summary

| | EC2 (our choice) | Lambda (stateless) |
|---|---|---|
| Connection pool | Persistent, in-memory, reused | Not possible without RDS Proxy |
| Startup logic | Runs once on container start | Must be moved to migrations/scripts |
| Cold starts | None (container always running) | 1–3s for heavy Python deps |
| Cost at low traffic | Fixed (~free tier) | Near zero (pay per invocation) |
| Cost at scale | Fixed (need more instances) | Scales automatically |
| Complexity | Low | Higher (API Gateway, RDS Proxy, stateless design) |
| Right choice when | Predictable, moderate traffic | Spiky, unpredictable, or near-zero baseline traffic |
