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
frontend/          → Next.js 14 app (placeholder until Day 13)
backend/app/       → FastAPI application
  enums.py         → All enums (central, never duplicate)
  config.py        → pydantic-settings (auto-loads .env)
  main.py          → FastAPI entry point
  api/routes/      → health.py, analysis.py
  providers/       → LLM and vector store abstractions (NEVER bypass these)
    llm/           → base.py, openai.py, anthropic.py, factory.py
    vectorstore/   → base.py, pinecone.py, factory.py
  agents/tools/    → Data fetching + calculations
  agents/          → LangChain orchestrator (Day 11+)
  rag/             → LlamaIndex RAG pipeline (Day 10+)
  models/          → domain.py, request.py, response.py
  services/        → Caching and shared services
backend/tests/     → pytest tests (conftest.py for shared fixtures)
bruno/             → API test collections (Bruno)
scripts/           → Utility scripts
docs/              → Documentation
```

## Current Architecture

| Module | Purpose | Key Files |
|--------|---------|-----------|
| `models/` | Pydantic domain, request & response models | `domain.py` (TechnicalAnalysis, FundamentalAnalysis, PriceData, etc.), `request.py`, `response.py` |
| `providers/llm/` | Swappable LLM abstraction (ABC + factory) | `base.py` (ChatMessage, LLMProvider), `openai.py`, `anthropic.py`, `factory.py` |
| `providers/vectorstore/` | Swappable vector store abstraction | `base.py` (Document, VectorStoreProvider), `pinecone.py`, `factory.py` |
| `agents/tools/` | Data fetching + indicator calculations | `stock_data.py` (yfinance wrapper), `technical.py` (RSI, MACD, SMA), `fundamentals.py` (valuation, profitability, growth, health scoring) |
| `api/routes/` | FastAPI endpoints | `health.py` (GET /health), `analysis.py` (POST /analyze — stub until Day 12) |
| `enums.py` | Central enum definitions | SignalType, MacdSignal, TrendDirection, VolumeTrend, provider types, etc. |
| `config.py` | Environment config | pydantic-settings, auto-loads `.env` |

## Coding Conventions

### Backend (Python)
- Python 3.11+, async/await everywhere
- Pydantic v2 for all data models
- Type hints on all function signatures
- **Enums for all string constants** — defined in `app/enums.py`, never use magic strings
- **Centralized field mappings** — external API keys mapped via module-level constants (e.g. `_YFINANCE_FIELD_MAP` in `fundamentals.py`), not inline strings
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
5. **Enums are centralized** — all in `app/enums.py`, used in models, providers, and factories

## Key Enums (app/enums.py)

- `ChatMessageRole` — SYSTEM, USER, ASSISTANT
- `LLMProviderType` — OPENAI, ANTHROPIC
- `VectorStoreProviderType` — PINECONE, QDRANT, PGVECTOR
- `DocumentType` — NEWS, FINANCIAL_REPORT, ANALYSIS, EARNINGS, SEC_FILING
- `SignalType` — BUY, HOLD, SELL
- `SentimentType` — POSITIVE, NEGATIVE, NEUTRAL, MIXED
- `OpenAIModel`, `AnthropicModel`, `OpenAIEmbeddingModel` — model identifiers
- `TrendDirection`, `MacdSignal`, `VolumeTrend` — technical analysis enums

## Testing

- **Framework:** pytest + pytest-asyncio (auto mode)
- **Config:** `backend/pytest.ini`
- **Fixtures:** `backend/tests/conftest.py` (mocked providers)
- **Run:** `cd backend && source venv/Scripts/activate && python -m pytest tests/ -v`
- **All tests are fully mocked** — no API keys required
- **API testing:** Bruno collections in `bruno/` (run with `bru run --env local`)

## Workflow Rules

- **Always update** [docs/PROGRESS_TRACKER.md](docs/PROGRESS_TRACKER.md) after completing a task (check the box, update counts and date)
- **Read before editing** — always read a file before modifying it
- **Test after building** — run relevant tests after implementing a feature
- **Don't over-engineer** — build what the spec says, no extra abstractions
