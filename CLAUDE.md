# CLAUDE.md — AI Assistant Context

> This file is loaded automatically at the start of every Claude Code session.
> Keep it concise and prescriptive. For full details, see docs/.

---

## Project Overview

**Stock Signal Advisor** — AI-powered stock analysis app providing Buy/Hold/Sell recommendations.
- **Frontend:** Next.js 14 (App Router) + TypeScript + Tailwind + shadcn/ui
- **Backend:** FastAPI (Python 3.11+) + LangChain + LlamaIndex
- **Hosting:** AWS Amplify (frontend) + AWS App Runner (backend)

## Key Documents

- [docs/STOCK_SIGNAL_ADVISOR_SPEC.md](docs/STOCK_SIGNAL_ADVISOR_SPEC.md) — Full project specification
- [docs/PROGRESS_TRACKER.md](docs/PROGRESS_TRACKER.md) — Development progress checklist

## Project Structure

```
frontend/          → Next.js 14 app
backend/app/       → FastAPI application
  providers/       → LLM and vector store abstractions (NEVER bypass these)
    llm/           → base.py, openai.py, anthropic.py, factory.py
    vectorstore/   → base.py, pinecone.py, factory.py
  agents/          → LangChain orchestrator and tools
  rag/             → LlamaIndex RAG pipeline
  models/          → Pydantic request/response/domain models
  services/        → Caching and shared services
  api/routes/      → FastAPI route handlers
bruno/             → API test collections (Bruno)
scripts/           → Utility scripts
docs/              → Documentation
```

## Coding Conventions

### Backend (Python)
- Python 3.11+, async/await everywhere
- Pydantic v2 for all data models
- Type hints on all function signatures
- Use `providers/` abstraction layer — never import openai/anthropic/pinecone directly in business logic
- FastAPI dependency injection for providers
- All endpoints under `/api/v1/` prefix

### Frontend (TypeScript)
- Next.js App Router (not Pages Router)
- Strict TypeScript — no `any` types
- Tailwind CSS for styling — no CSS modules or styled-components
- shadcn/ui for UI components
- React Query (TanStack) for all API calls
- Types defined in `types/index.ts`

### General
- Environment variables via `.env` — never hardcode secrets
- Meaningful commit messages (conventional commits preferred)

## Architecture Rules

1. **Provider abstraction is mandatory** — all LLM calls go through `providers/llm/base.py` interface, all vector store calls through `providers/vectorstore/base.py`
2. **Factory pattern for providers** — use `factory.py` to instantiate, driven by config
3. **Three analysis pillars** — Technical (35%), Fundamental (35%), Sentiment (30%)
4. **Cache aggressively** — use TTL-based in-memory cache for API responses

## Workflow Rules

- **Always update** [docs/PROGRESS_TRACKER.md](docs/PROGRESS_TRACKER.md) after completing a task (check the box, update counts and date)
- **Read before editing** — always read a file before modifying it
- **Test after building** — run relevant tests after implementing a feature
- **Don't over-engineer** — build what the spec says, no extra abstractions
