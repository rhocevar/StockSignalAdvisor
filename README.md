# Stock Signal Advisor

[![CI/CD](https://github.com/rhocevar/StockSignalAdvisor/actions/workflows/ci.yml/badge.svg)](https://github.com/rhocevar/StockSignalAdvisor/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![Next.js](https://img.shields.io/badge/Next.js-14-black)

AI-powered stock analysis app that delivers **Buy / Hold / Sell** recommendations backed by technical analysis, fundamental metrics, and news sentiment — with full source transparency.

<p align="center">
  <img src="docs/demo.gif" alt="Stock Signal Advisor Demo" width="800">
</p>

## Live Demo

- **Frontend:** https://main.d3gra918usm0j6.amplifyapp.com
- **API Health:** https://xdvpqzqg4m.us-east-2.awsapprunner.com/api/v1/health

## Features

- **Three-pillar analysis** — Technical (RSI, MACD, moving averages), Fundamental (P/E, margins, growth), and Sentiment (news headlines via LLM) are individually scored and weighted into a final recommendation
- **LangChain ReAct agent** — a reasoning agent with 6 tools that autonomously gathers data, consults RAG context, and produces an explanation
- **RAG-augmented analysis** — Pinecone vector store with 18 financial knowledge documents provides domain context for the agent's reasoning
- **Real-time market data** — yfinance for price, technicals, and fundamentals; NewsAPI for headlines
- **Provider abstraction** — swap OpenAI ↔ Anthropic and Pinecone ↔ Qdrant ↔ pgvector with a single config change
- **TTL caching** — results cached for 1 hour to minimize API costs
- **SSR frontend** — Next.js 14 App Router with server-side rendering, deployed on AWS Amplify

## Architecture

```
Browser
  └── AWS Amplify (Next.js 14 SSR)
        └── POST /api/v1/signal
              └── AWS App Runner (FastAPI)
                    └── StockAnalysisOrchestrator
                          ├── Technical pillar  ──→ yfinance
                          ├── Fundamental pillar ─→ yfinance
                          ├── Sentiment pillar ──→ NewsAPI + OpenAI
                          └── LangChain Agent
                                ├── 6 tools (price, technicals, fundamentals,
                                │          news, sentiment, RAG search)
                                └── Pinecone (RAG vector store)
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full system design.

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | Next.js 14 (App Router), TypeScript, Tailwind CSS, shadcn/ui, React Query |
| **Backend** | FastAPI, Python 3.11+, Pydantic v2, asyncio |
| **AI / Agents** | LangChain, LangGraph, OpenAI GPT-4o-mini (swappable to Anthropic) |
| **Vector Store** | Pinecone (swappable to Qdrant / pgvector) |
| **Data Sources** | yfinance, NewsAPI |
| **Infrastructure** | AWS App Runner, AWS Amplify, Docker, Amazon ECR |
| **CI/CD** | GitHub Actions |

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker (optional — for the one-command setup)
- API keys: [OpenAI](https://platform.openai.com/api-keys), [Pinecone](https://app.pinecone.io/), [NewsAPI](https://newsapi.org/register)

### 1. Clone and configure

```bash
git clone https://github.com/rhocevar/StockSignalAdvisor.git
cd StockSignalAdvisor
cp .env.example .env
# Edit .env and fill in your API keys
```

### 2a. Docker (recommended)

```bash
docker compose up
```

Backend at `http://localhost:8000`, frontend at `http://localhost:3000`.

### 2b. Manual setup

**Backend:**
```bash
cd backend
python -m venv venv
source venv/Scripts/activate   # Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend** (new terminal):
```bash
cd frontend
npm install
# Create frontend/.env.local with:
# NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

### 3. Seed Pinecone (first time only)

```bash
cd backend
source venv/Scripts/activate
python -m scripts.seed_pinecone
```

### 4. Pre-warm the cache (optional)

```bash
python scripts/precache.py
# or against production:
python scripts/precache.py --url https://xdvpqzqg4m.us-east-2.awsapprunner.com
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `LLM_PROVIDER` | Yes | `openai` or `anthropic` |
| `LLM_MODEL` | Yes | e.g. `gpt-4o-mini` or `claude-3-5-haiku-20241022` |
| `OPENAI_API_KEY` | If using OpenAI | OpenAI API key |
| `ANTHROPIC_API_KEY` | If using Anthropic | Anthropic API key |
| `VECTORSTORE_PROVIDER` | Yes | `pinecone` |
| `PINECONE_API_KEY` | Yes | Pinecone API key |
| `PINECONE_INDEX_NAME` | Yes | e.g. `stock-signal-advisor` |
| `NEWS_API_KEY` | Yes | NewsAPI key |
| `CACHE_TTL_SECONDS` | No | Cache TTL in seconds (default: 3600) |
| `CORS_ORIGINS` | No | JSON array of allowed origins |
| `NEXT_PUBLIC_API_URL` | Yes (frontend) | Backend URL for the Next.js app |

See `.env.example` for the full template.

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/health` | GET | Service health + provider status |
| `/api/v1/signal` | POST | Full stock analysis → Buy/Hold/Sell |
| `/api/v1/tools/stock-price/{ticker}` | GET | Current price and 52-week range |
| `/api/v1/tools/company-name/{ticker}` | GET | Company name lookup |
| `/api/v1/tools/technicals/{ticker}` | GET | RSI, MACD, SMA indicators |
| `/api/v1/tools/fundamentals/{ticker}` | GET | P/E, margins, growth metrics |
| `/api/v1/tools/news/{ticker}` | GET | Recent news headlines |
| `/api/v1/tools/sentiment/{ticker}` | GET | LLM-classified news sentiment |
| `/api/v1/tools/rag-search` | GET | Semantic search over financial knowledge |

Full documentation: [docs/API.md](docs/API.md)
Interactive docs (local only): `http://localhost:8000/docs`

## Running Tests

### Backend (pytest)

```bash
cd backend
source venv/Scripts/activate   # Linux/Mac: source venv/bin/activate
python -m pytest tests/ -v
```

All 230+ tests are fully mocked — no API keys required.

### Frontend (Jest)

```bash
cd frontend
npm test
```

### API Tests (Bruno)

```bash
# Install Bruno: https://www.usebruno.com/downloads
bru run --env local              # All tests
bru run analysis --env local     # Analysis endpoint only
```

## Deployment

The app deploys to AWS:
- **Backend** → AWS App Runner via Docker image on Amazon ECR
- **Frontend** → AWS Amplify (Next.js SSR, auto-deploys on push to `main`)
- **CI/CD** → GitHub Actions runs tests, builds and pushes Docker image, and verifies the deployment

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#deployment-architecture) for the full deployment setup.

## Project Structure

```
.github/workflows/   GitHub Actions CI/CD pipeline
backend/
  app/
    api/routes/      FastAPI route handlers (health, signal, tools)
    agents/          LangChain orchestrator + 6 analysis tools
    models/          Pydantic models (domain, request, response)
    providers/       Swappable LLM + vector store abstractions
    rag/             RAG pipeline (embeddings, indexer, retriever)
    services/        TTL cache
    enums.py         Centralized string constants
    config.py        pydantic-settings (auto-loads .env)
    main.py          FastAPI entry point
  scripts/           seed_pinecone.py — index seed documents
  tests/             230+ pytest unit tests (fully mocked)
bruno/               Bruno API test collections
docs/                API.md, ARCHITECTURE.md, spec, progress tracker
frontend/
  src/
    app/             Next.js App Router pages (home, analyze/[ticker])
    components/      UI components (SignalCard, PriceChart, etc.)
    hooks/           useAnalysis React Query hook
    lib/             API client
    types/           TypeScript interfaces
scripts/             precache.py — cache warm-up for demo
```

## Disclaimer

For **educational and demonstration purposes only**. Not financial advice. Always do your own research before making investment decisions.

## License

[MIT](LICENSE)
