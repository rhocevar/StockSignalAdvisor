# Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────┐
│                      Browser                            │
└────────────────────────┬────────────────────────────────┘
                         │ HTTPS
┌────────────────────────▼────────────────────────────────┐
│              AWS Amplify (Next.js 14 SSR)               │
│         https://main.d3gra918usm0j6.amplifyapp.com      │
│                                                         │
│  / (home)           → TickerInput                       │
│  /analyze/[ticker]  → AnalysisView (React Query)        │
└────────────────────────┬────────────────────────────────┘
                         │ POST /api/v1/signal
┌────────────────────────▼────────────────────────────────┐
│           AWS App Runner (FastAPI + Docker)              │
│        https://xdvpqzqg4m.us-east-2.awsapprunner.com   │
│                                                         │
│  StockAnalysisOrchestrator                              │
│    ├── TTL Cache (cachetools, 1h)                       │
│    ├── Technical pillar ──────────────→ yfinance        │
│    ├── Fundamental pillar ────────────→ yfinance        │
│    ├── Sentiment pillar ──────────────→ NewsAPI         │
│    └── LangChain ReAct Agent                            │
│          ├── 6 tools (see below)                        │
│          └── RAG context ────────────→ Pinecone         │
└────────────────────────┬────────────────────────────────┘
                         │
          ┌──────────────┼──────────────┐
          │              │              │
     ┌────▼───┐    ┌─────▼────┐  ┌─────▼────┐
     │OpenAI  │    │ Pinecone │  │ yfinance │
     │GPT-4o  │    │ (RAG +   │  │ NewsAPI  │
     │  mini  │    │ embedds) │  │          │
     └────────┘    └──────────┘  └──────────┘
```

---

## Three-Pillar Analysis

The core of the recommendation engine. Each pillar produces a score from 0.0 (bearish) to 1.0 (bullish), then they are weighted to produce the final confidence score.

### Pillar Weights

| Available pillars | Technical | Fundamental | Sentiment |
|-------------------|-----------|-------------|-----------|
| All three | 40% | 40% | 20% |
| No fundamentals | 70% | — | 30% |
| No sentiment | 60% | 40% | — |
| Technical only | 100% | — | — |

### How Scores Combine

```
confidence = Σ (pillar_score × pillar_weight)
```

The LangChain agent's own signal (STRONG_BUY/BUY/HOLD/SELL/STRONG_SELL) determines the recommendation direction; the orchestrator computes the weighted confidence independently from pillar scores.

### Scoring Logic

**Technical score** (`agents/tools/technical.py`):
- RSI: >70 overbought (bearish), <30 oversold (bullish), 30–70 neutral
- Price vs 50/200-day SMA: above = bullish
- MACD: bullish/bearish crossover
- Volume trend: increasing volume reinforces signal direction

**Fundamental score** (`agents/tools/fundamentals.py`):
- Valuation multiples (P/E, PEG, P/B) vs sector medians
- Profitability (profit margin, ROE, ROA)
- Growth rates (revenue, earnings)
- Financial health (current ratio, debt/equity)
- Analyst consensus (target vs current price, rating)

**Sentiment score** (`agents/tools/sentiment.py`):
- LLM classifies each headline as POSITIVE / NEGATIVE / NEUTRAL
- Score = positive_count / total_count (with NEUTRAL counted at 0.5)

---

## Provider Abstraction

All external AI service calls go through abstract base classes. No business logic imports OpenAI, Anthropic, or Pinecone directly.

```
providers/
  llm/
    base.py        ← ABC: ChatMessage, LLMProvider, LLMRateLimitError
    openai.py      ← OpenAIProvider(LLMProvider)
    anthropic.py   ← AnthropicProvider(LLMProvider)
    factory.py     ← create_llm_provider(settings) → LLMProvider
  vectorstore/
    base.py        ← ABC: Document, SearchResult, VectorStoreProvider
    pinecone.py    ← PineconeProvider(VectorStoreProvider)
    factory.py     ← create_vectorstore_provider(settings) → VectorStoreProvider
```

**Swapping providers** requires only a config change:
```bash
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-5-haiku-20241022
```

---

## LangChain ReAct Agent

The agent (`agents/agent.py`) uses LangGraph's runtime with `create_agent` to implement a ReAct (Reasoning + Acting) loop. It has access to 6 tools and produces a structured `AgentResult` (signal + confidence + explanation).

### Agent Tools

| Tool | Description | Data source |
|------|-------------|-------------|
| `get_stock_price` | Current price, 52w range, history | yfinance |
| `get_company_info` | Name, sector, industry | yfinance |
| `calculate_technicals` | RSI, MACD, SMA, volume | yfinance |
| `get_fundamentals` | P/E, margins, growth, analyst data | yfinance |
| `get_news_sentiment` | Headlines + LLM sentiment | NewsAPI + OpenAI |
| `search_financial_context` | RAG search over knowledge base | Pinecone |

### Agent Execution Flow

```
1. Orchestrator calls run_agent(ticker, context)
2. Agent receives system prompt with three-pillar framework
3. Agent iteratively calls tools (ReAct loop)
4. Agent consults RAG for domain context
5. Agent synthesizes STRONG_BUY/BUY/HOLD/SELL/STRONG_SELL + explanation
6. Orchestrator parses AgentResult, computes weighted confidence
```

---

## RAG Pipeline

Retrieval-Augmented Generation provides the agent with relevant financial domain knowledge, improving reasoning quality without requiring the LLM to memorize financial rules.

```
Indexing (one-time, scripts/seed_pinecone.py):
  18 documents → generate_embedding() → Pinecone upsert

Query (per analysis):
  query string → generate_embedding() → Pinecone query
              → top-k SearchResult → injected into agent context
```

### Knowledge Base (18 documents)

| Category | Topics |
|----------|--------|
| Technical analysis | RSI overbought/oversold, MACD crossovers, SMA trends, volume confirmation |
| Fundamental analysis | P/E interpretation, PEG ratio, debt-to-equity, ROE benchmarks, FCF |
| Sector guidance | Technology, utilities, financials — sector-specific valuation norms |
| Risk assessment | Beta, 52-week range positioning, diversification principles |

### RAG Components

- `rag/embeddings.py` — `generate_embedding(text)`, `embed_documents(docs)`
- `rag/indexer.py` — `index_documents(docs)`, `delete_documents(ids)`
- `rag/retriever.py` — `retrieve(query, top_k)`, `retrieve_context(query)` → formatted string

---

## Caching Strategy

Results are cached in-memory using `cachetools.TTLCache` (`services/cache.py`).

| Property | Value |
|----------|-------|
| Storage | In-process memory (not Redis) |
| TTL | 3600 seconds (1 hour), configurable via `CACHE_TTL_SECONDS` |
| Key | Ticker symbol (uppercase) |
| Return | Deep copy (`model_copy(deep=True)`) to prevent mutation of cached objects |

**Trade-offs:**
- Resets on every App Runner restart / redeploy
- Not shared across multiple instances (scale-out → cache misses)
- Ideal for single-instance deployment; for multi-instance, replace with Redis

**Warm-up:** `scripts/precache.py` pre-loads popular tickers immediately after deployment.

---

## Data Sources

### yfinance

Used for: price data, technical indicator inputs (OHLCV), and all fundamental metrics.

All tool functions accept a `yf.Ticker` object (created once per request by `get_ticker()` in `agents/tools/stock_data.py`) to avoid redundant network calls.

**Known yfinance quirks:**
- `debtToEquity` is returned as a percentage — divided by 100 in `fundamentals.py`
- `dividendYield` (≥1.0) is returned as a percentage — divided by 100
- Some fields are `None` for ETFs or foreign stocks — all fields are nullable in `FundamentalAnalysis`

### NewsAPI

Used for: recent news headlines for the sentiment pillar and `sources` list in the response.

Headlines are fetched by ticker + company name query. Up to 10 articles are retrieved and passed to the LLM for classification.

---

## Frontend Architecture

### Stack

- **Next.js 14** App Router — SSR for fast initial load, client components for interactivity
- **React Query** (`useQuery`) — analysis triggered on mount, deduplicated by ticker key
- **shadcn/ui** — accessible component primitives (Button, Card, Input, Badge)
- **Recharts** — price history line chart (`PriceChart` component)
- **Tailwind CSS** — utility-first styling

### Component Hierarchy

```
/ (page.tsx)
  └── TickerInput          ← search input + submit, navigates to /analyze/[ticker]

/analyze/[ticker] (page.tsx)
  └── AnalysisView         ← client component, owns React Query mutation
        ├── LoadingState   ← animated spinner + cycling status messages
        ├── [error panel]  ← inline error with Try Again button
        └── [results]
              ├── SignalCard          ← STRONG_BUY/BUY/HOLD/SELL/STRONG_SELL + confidence + price
              │     └── SignalBadge  ← colored badge
              ├── PriceChart         ← 30-day line chart (Recharts)
              ├── TechnicalIndicators← RSI, MACD, SMA, volume trend
              ├── FundamentalsCard   ← valuation, profitability, growth tables
              ├── ExplanationPanel   ← LLM explanation text
              ├── SourcesList        ← news headlines with sentiment badges
              └── Disclaimer         ← non-financial-advice notice
```

### Data Flow

```
User types ticker → TickerInput → router.push("/analyze/AAPL")
Page loads → AnalysisView mounts → useAnalysis("AAPL") returns { isPending, data, error, refetch }
React Query fires fetch POST /api/v1/signal → backend (deduplicated for same ticker)
Response → React Query updates state → components re-render with data
```

---

## Deployment Architecture

```
Developer pushes to main
        │
        ▼
GitHub Actions (ci.yml)
  ├── backend job: pytest (230+ tests, fully mocked)
  ├── frontend job: lint + jest + next build
  └── deploy job (after both pass):
        ├── docker build ./backend
        ├── docker push → Amazon ECR
        └── App Runner auto-detects new image → rolling deploy
              └── smoke-test job: poll describe-service until RUNNING
                    └── curl /api/v1/health → assert 200

Amplify:
  GitHub push → Amplify webhook → npm ci + npm run build → SSR deploy
```

### AWS Services

| Service | Purpose | Config file |
|---------|---------|-------------|
| AWS App Runner | Backend container hosting (auto-scaling, HTTPS) | `backend/apprunner.yaml` (reference only) |
| Amazon ECR | Docker image registry | hardcoded in `ci.yml` |
| AWS Amplify | Frontend SSR hosting + CDN | `frontend/amplify.yml` |
| GitHub Actions | CI/CD orchestration | `.github/workflows/ci.yml` |

### Environment Variables in Production

- **App Runner:** set in AWS console under "Environment variables" (plain text, not Secrets Manager)
- **Amplify:** `NEXT_PUBLIC_API_URL` set in Amplify console → App Settings → Environment Variables
- **CORS:** `CORS_ORIGINS` on App Runner must include the Amplify app URL
