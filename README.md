# Stock Signal Advisor

AI-powered stock analysis app that provides **Buy / Hold / Sell** recommendations with transparent explanations.

Enter a ticker, get a recommendation backed by technical analysis, fundamental metrics, and news sentiment — with full source transparency.

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | Next.js 14, TypeScript, Tailwind CSS, shadcn/ui, React Query |
| **Backend** | FastAPI, Python 3.11+, Pydantic v2 |
| **AI/ML** | LangChain, LlamaIndex, OpenAI (GPT-4o-mini) |
| **Vector Store** | Pinecone (with provider abstraction for Qdrant/pgvector) |
| **Data** | yfinance, NewsAPI |
| **Infrastructure** | AWS App Runner, AWS Amplify, Docker |

## Architecture

```
User → Next.js Frontend → FastAPI Backend → LangChain Orchestrator
                                                 ├── Technical Analysis (RSI, MACD, SMA)
                                                 ├── Fundamental Analysis (P/E, ROE, growth)
                                                 ├── Sentiment Analysis (news headlines)
                                                 └── RAG Context (Pinecone + LlamaIndex)
```

**Key design pattern:** Provider abstraction layers allow swapping LLM providers (OpenAI ↔ Anthropic) and vector stores (Pinecone ↔ Qdrant ↔ pgvector) with a single config change.

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker (optional)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example ../.env      # Fill in your API keys
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Docker

```bash
cp .env.example .env            # Fill in your API keys
docker compose up
```

## API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/health` | GET | Health check + provider status |
| `/api/v1/analyze` | POST | Analyze a stock ticker |

See [docs/API.md](docs/API.md) for full API documentation.

## Project Structure

```
frontend/           Next.js 14 application
backend/            FastAPI application
  app/
    api/routes/     Route handlers
    providers/      LLM + vector store abstractions
    agents/         LangChain orchestrator + tools
    rag/            RAG pipeline (LlamaIndex)
    models/         Pydantic models
    services/       Caching + shared services
bruno/              API test collections
docs/               Documentation
scripts/            Utility scripts
```

## Disclaimer

This application is for **educational and demonstration purposes only**. It is not financial advice. Always do your own research before making investment decisions.

## License

[MIT](LICENSE)
