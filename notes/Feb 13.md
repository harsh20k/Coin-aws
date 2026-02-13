[[schema]]


## Recommended Approach: Local-First, Early Cloud Integration

- **Develop Locally**
  - Use React dev server, local DB, and local API (or Lambda emulator).
  - Configure via env vars to switch between local and cloud resources.

- **Integrate Cloud Early**
  - Use real Cognito (or a dev pool) from the start to match auth with production.
  - Optionally, use a shared dev RDS/DynamoDB and a single dev Lambda + API Gateway once the API is stable.

- **Deploy Frequently**
  - As soon as the app works end-to-end, set up a basic deploy pipeline (git push → build → deploy to AWS dev/staging).
  - Catch deployment and environment issues early.

---

### Why NOT 100% Local?
- Cloud-specific issues (CORS, IAM, API Gateway, Cognito URLs) appear late.
- “Works on my machine” can hide config/permissions problems.

### Why NOT 100% Cloud?
- Slower feedback (must deploy every change).
- Potential costs and harder debugging.
- Local is faster for UI/business logic work.

---

## For Dalla / This Course

- Build locally (React, Node/Lambda, SQL/DynamoDB).
- Use real Cognito early (dev user pool, localhost callbacks).
- Once core flow works, add IaC and one-command deploy.
- Continue working via this pipeline for the rest of the project.

**Summary:**  
Work mostly local, bring in key cloud services (like Cognito) early, and set up an early deploy path.

## Screens / Pages

**Core:**
- **Auth:** Login/Sign Up.
- **Dashboard:** Wallet summary, recent transactions, budgets/goals overview.
- **Wallets:** View, add, select wallets.
- **Transactions:** List/filter; add/edit (type, subcategory, amount, description, tags, date).
- **Budgets:** List/add/edit (category, limit, period).
- **Goals:** List/add/edit (title, target, type, period), track progress.
- **Insights/AI Chat:** Conversational Q&A about spending, budgets, goals.

**Optional:**
- **Settings:** Profile, default categories, preferences.
- **Subcategories:** Manage or customize subcategories.

---

**SPA Approach:**  
Use a single-page app with client-side routing (e.g., React Router) for views like `/`, `/wallets`, `/transactions`, `/budgets`, `/goals`, `/chat`. All pages live in one HTML shell; don’t create separate HTML files.

## Actions required 

**Login / Sign up**
  - Sign in
  - Sign up
  - Forgot password

**Dashboard**
  - Switch wallet
  - Add transaction
  - Navigate to Wallets, Transactions, Budgets, Goals, Chat

**Wallets**
  - Create wallet
  - Edit wallet
  - Delete wallet
  - Select wallet

**Transactions**
  - Add transaction
  - Edit
  - Delete
  - Filter (date, type, subcategory, tags)

**Budgets**
  - Create budget
  - Edit
  - Delete
  - Filter by period

**Goals**
  - Create goal
  - Edit
  - Delete
  - Mark complete / cancel
  - Filter by period

**AI chat**
  - Send message
  - Clear conversation
  - (optional) Suggested prompts

**Global**
  - Log out
  - Navigation links (Dashboard, Wallets, Transactions, Budgets, Goals, Chat)
