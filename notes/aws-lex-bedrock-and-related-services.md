# AWS Lex, Bedrock, and Related AI Services

Quick reference for choosing and combining AWS conversational/generative AI services.

---

## Amazon Lex

**Purpose:** Build **conversational bots** (chat and voice) with structured intent/slot flows.

- **Model:** Intent + slots; you define intents, sample utterances, slot types, and conversation paths.
- **Flow:** Lex manages the dialogue (slot elicitation, validation, confirmation). Optional Lambda for business logic.
- **Lex V2:** Custom conversation paths, conditional branching, next-step config; no Lambda required for simple flows.
- **Best for:** Customer service bots, FAQ automation, order/booking flows, IVR-style voice bots.
- **Limitation:** Not generative—responses are from your intents/prompts and Lambda, not free-form LLM output.

---

## Amazon Bedrock

**Purpose:** **Generative AI** via foundation models (LLMs) and related tooling; single API for multiple model providers.

- **Model:** Access to FMs from Anthropic (Claude), AI21, Cohere, Meta, Mistral, Stability, Amazon (Titan).
- **No infra:** Managed; no GPU/server setup.
- **Key features:**
  - **Foundation models:** Invoke models for chat, completion, embeddings.
  - **Knowledge Bases:** RAG over your data (S3, Confluence, Salesforce, etc.); vector stores (OpenSearch, Aurora, Pinecone, etc.). Optional GraphRAG.
  - **Agents:** Autonomous agents that call APIs, query knowledge bases, and use FMs to complete tasks (e.g. claims, reservations).
- **Best for:** Content generation, summarization, Q&A over docs, agents, embeddings—anything that needs LLM output or RAG.

---

## Lex vs Bedrock (summary)

| Aspect        | Lex                          | Bedrock                               |
|---------------|------------------------------|----------------------------------------|
| **Role**      | Conversational flow + NLU    | LLM access + RAG + agents              |
| **Responses** | Intent/slot + your logic     | Generative (model output)              |
| **Design**    | Intents, slots, paths        | Prompts, knowledge bases, agent steps  |
| **Use case**  | Bots with clear flows        | Open-ended generation, RAG, automation |

They **complement** each other: Lex can use **Bedrock Knowledge Bases** via **QnAIntent** so a Lex bot answers from your data with RAG, while Lex still handles the conversational flow and routing.

---

## Related AWS AI Services

- **Amazon Transcribe:** Speech → text (ASR). Real-time and batch; 100+ languages. Use with voice input before Lex or Bedrock.
- **Amazon Polly:** Text → speech (TTS). Many voices/languages; SSML. Use for voice output after Lex or Bedrock.
- **Amazon Comprehend:** NLP (entities, sentiment, PII, topic modeling). Use for analysis of text before/after Lex or Bedrock.
- **Amazon SageMaker:** Train and deploy custom ML models (including some LLMs). Use when you need your own models; Bedrock is for managed FMs.
- **Amazon Kendra:** Enterprise search with ML. Alternative/complement to Bedrock Knowledge Bases for search-style Q&A.

**Typical voice pipeline:** Transcribe (speech→text) → Lex or Bedrock (understanding/generation) → Polly (text→speech).

---

## For Dalla (Chat feature)

- **Bedrock** fits “AI conversation” over user data (wallets, transactions, budgets, goals): use a Bedrock FM + optional Knowledge Base or your API as context.
- **Lex** fits if you later add a **guided** flow (e.g. “create a goal” or “log a transaction” step-by-step) with intent/slots; you can still back specific intents with Bedrock (e.g. QnAIntent + Knowledge Base).
