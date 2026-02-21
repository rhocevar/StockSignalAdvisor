# CLAUDE.md — AI Assistant Context

> This file is loaded automatically at the start of every Claude Code session.
> Keep it concise and prescriptive. For full details, see docs/.

---

## Project Overview

**Stock Signal Advisor** — AI-powered stock analysis app providing Buy/Hold/Sell recommendations.
- **Frontend:** Next.js 14 (App Router) + TypeScript + Tailwind + shadcn/ui + Recharts v3.7.0
- **Backend:** FastAPI (Python 3.11+) + LangChain + LangGraph
- **Hosting:** AWS Amplify (frontend) + AWS App Runner (backend)

## Key Documents

- [docs/API.md](docs/API.md) — Full API reference
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — System design

## Project Structure

```
frontend/          → Next.js 14 app (App Router + TypeScript + Tailwind + shadcn/ui)
  src/app/         → App Router pages (home, analyze/[ticker])
  src/components/  → providers.tsx (React Query), ui/ (shadcn/ui components)
  src/types/       → TypeScript types mirroring backend Pydantic models
  src/lib/         → api.ts (fetch-based API client)
  src/hooks/       → useAnalysis.ts (React Query mutation hook)
  .agents/skills/  → Vercel Agent Skills (react-best-practices, etc.)
backend/app/       → FastAPI application
  enums.py         → All enums (central, never duplicate)
  config.py        → pydantic-settings (auto-loads .env)
  main.py          → FastAPI entry point
  api/routes/      → health.py, analysis.py, tools.py
  providers/       → LLM and vector store abstractions (NEVER bypass these)
    llm/           → base.py, openai.py, anthropic.py, factory.py
    vectorstore/   → base.py, pinecone.py, factory.py
  agents/tools/    → Data fetching + calculations + sentiment
  agents/prompts.py → System prompts (analysis, sentiment)
  agents/          → LangChain orchestrator
  rag/             → Embedding pipeline + indexer + retriever
  models/          → domain.py, request.py, response.py
  services/        → Caching and shared services
backend/tests/     → pytest tests (conftest.py for shared fixtures)
bruno/             → API test collections (Bruno)
backend/scripts/   → Utility scripts (seed_pinecone.py)
scripts/           → Root-level scripts (.gitkeep)
docs/              → Documentation
```

## Current Architecture

| Module | Purpose | Key Files |
|--------|---------|-----------|
| `models/` | Pydantic domain, request & response models | `domain.py` (TechnicalAnalysis, FundamentalAnalysis, PriceData, etc.), `request.py`, `response.py` |
| `providers/llm/` | Swappable LLM abstraction (ABC + factory) | `base.py` (ChatMessage, LLMProvider, LLMRateLimitError), `openai.py`, `anthropic.py`, `factory.py` |
| `providers/vectorstore/` | Swappable vector store abstraction | `base.py` (Document, VectorStoreProvider), `pinecone.py`, `factory.py` |
| `agents/tools/` | Data fetching + indicator calculations | `stock_data.py` (yfinance wrapper), `technical.py` (RSI, MACD, SMA), `fundamentals.py` (scoring), `sentiment.py` (LLM sentiment) |
| `agents/prompts.py` | System prompts for LLM calls | `ANALYSIS_SYSTEM_PROMPT` (three-pillar), `SENTIMENT_SYSTEM_PROMPT` (headline classification) |
| `agents/agent.py` | LangChain ReAct agent | `run_agent(ticker)` → BUY/HOLD/SELL via `create_agent` (LangGraph), 6 tools |
| `agents/orchestrator.py` | Analysis orchestrator | `StockAnalysisOrchestrator.analyze()` — parallel data gathering, shared yf.Ticker, dynamic pillar reweighting, caching |
| `services/cache.py` | TTL cache | `get_cached()`, `set_cached()`, `clear_cache()` — cachetools.TTLCache keyed by ticker |
| `rag/` | RAG pipeline (embed, index, retrieve) | `embeddings.py` (generate_embedding, embed_documents), `indexer.py` (index_documents, delete_documents), `retriever.py` (retrieve, retrieve_context) |
| `api/routes/` | FastAPI endpoints | `health.py`, `analysis.py` (wired to orchestrator), `tools.py` (individual tool test endpoints + sentiment) |
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
3. **Three analysis pillars** — Technical (40%), Fundamental (40%), Sentiment (20%) — dynamic reweighting when pillars unavailable
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

- **Read before editing** — always read a file before modifying it
- **Test after building** — run relevant tests after implementing a feature
- **Don't over-engineer** — no extra abstractions beyond what is needed
