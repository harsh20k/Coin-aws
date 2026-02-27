## Bedrock usage — coinBaby AI advisor

### Current implementation (baseline)

- **Model**: `global.anthropic.claude-haiku-4-5-20251001-v1:0` via Bedrock Runtime.
- **Pattern**: For each `/chat` request, backend:
  - Loads wallets, last ~50 transactions, budgets, and goals from Postgres.
  - Serializes all of that into a big text block.
  - Appends the user’s question.
  - Sends a single `user` message plus a `system` persona prompt to Bedrock.
- **Issues**:
  - Every request re-sends a large chunk of data, even if the user is asking a simple follow-up.
  - No real *conversation memory* — each turn is basically stateless.
  - Token/cost and latency scale with the size of the raw data dump, not with what’s relevant.

### Industry-standard patterns for this use case

- **1. Conversation memory (chat history)**
  - Maintain a per-session message history (`[system, user, assistant, …]`) and send *recent turns*, not just the latest question.
  - Only load and send the full financial context on the **first** turn (or when context needs refreshing).
  - Subsequent turns: send just the new user message plus enough recent history for coherence.

- **2. Summarized financial context instead of raw rows**
  - Pre-aggregate:
    - Net worth snapshot.
    - Spend by category (this month / last month).
    - Budget utilization and goal progress.
  - Only fetch and include raw transactions when the question needs it (e.g., “What did I spend on food last week?”).
  - This keeps prompts short, focused, and cheaper.

- **3. Tool / function calling over the financial DB**
  - Give the model tools like:
    - `get_budget_summary()`
    - `get_goal_progress(goal_id)`
    - `get_transactions(start_date, end_date, category)`
  - The LLM decides which tool to call, gets structured JSON back, and then answers.
  - This is the **industry-standard pattern** for apps with structured per-user data (personal finance, CRMs, analytics dashboards).

- **4. Where RAG fits (and doesn’t)**
  - **RAG is great** for large, unstructured document corpora (filings, PDFs, research reports, general knowledge bases).
  - Our use case is **small-to-medium, structured, relational data** already well-served by SQL and tool calls.
  - For coinBaby:
    - RAG is **not** the main value-add for per-user transaction data.
    - It would make sense later if we add a *knowledge base* (articles on budgeting, investing, FAQs) and want Penny to cite/support answers from that corpus.

### Recommended target architecture for Penny

- **Short term**
  - Add conversation history in `/chat` so Penny remembers prior turns.
  - Switch from “dump all rows” to “send summary + only relevant detail”.

- **Medium term**
  - Add Bedrock function-calling style tools over the financial DB so the model pulls exactly what it needs.
  - Optionally, introduce a small knowledge base (RAG) for general finance education content, separate from per-user data.

