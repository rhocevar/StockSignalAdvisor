# Stock Signal Advisor - Project Specification

> **Purpose:** This document provides complete context for building an AI-powered stock analysis tool. Use this as the foundational context when working with Cursor IDE or any AI coding assistant.

---

## 🎯 Project Overview

**Stock Signal Advisor** is an AI-powered web application that analyzes stock tickers and provides actionable Buy/Hold/Sell recommendations with transparent explanations.

### Core User Flow
1. User enters a stock ticker (e.g., `VOO`, `AAPL`, `NVDA`)
2. System fetches real-time data from multiple sources
3. AI agent analyzes technical indicators, fundamentals, and news sentiment
4. User receives: **Buy / Hold / Sell** recommendation + detailed explanation
5. Sources and reasoning are displayed transparently

### Target Audience
- Retail investors seeking AI-assisted analysis
- Recruiters/hiring managers evaluating the developer's AI engineering skills
- Non-technical users who want simple, explainable insights

### Project Goals
- **Primary:** Showcase AI engineering skills (RAG, agents, LLM orchestration)
- **Secondary:** Demonstrate full-stack development (React/Next.js, FastAPI)
- **Tertiary:** Gain AWS deployment experience

### Architecture Principles
- **Provider-agnostic:** Abstract LLM and vector store providers for easy swapping
- **Cost-effective:** Use free tiers where possible, cache aggressively
- **Demo-ready:** Fast responses, clean UI, impressive to non-technical viewers
- **Future-proof:** Easy to add auth, subscriptions, and more analysis types later

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                           FRONTEND                                  │
│                  Next.js 14 (App Router) + TypeScript               │
│                       Hosted on AWS Amplify                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────┐ │
│  │ Ticker Input│  │ Signal Card │  │ Explanation + Sources Panel │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      AWS CLOUD (Backend)                            │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    AWS App Runner                            │   │
│  │                  FastAPI (Python 3.11+)                      │   │
│  │                                                              │   │
│  │  ┌──────────────────────────────────────────────────────┐   │   │
│  │  │              ABSTRACTION LAYERS                       │   │   │
│  │  │  ┌─────────────────┐    ┌─────────────────────────┐  │   │   │
│  │  │  │  LLM Provider   │    │   Vector Store Provider │  │   │   │
│  │  │  │  ─────────────  │    │   ───────────────────── │  │   │   │
│  │  │  │  • OpenAI  ✓    │    │   • Pinecone  ✓         │  │   │   │
│  │  │  │  • Anthropic    │    │   • Qdrant              │  │   │   │
│  │  │  │  • Local (future│    │   • pgvector            │  │   │   │
│  │  │  └─────────────────┘    └─────────────────────────┘  │   │   │
│  │  └──────────────────────────────────────────────────────┘   │   │
│  │                                                              │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │   │
│  │  │ Data Fetcher │  │   Analysis   │  │   RAG Engine     │   │   │
│  │  │   Agent      │  │    Agent     │  │  (LlamaIndex)    │   │   │
│  │  └──────────────┘  └──────────────┘  └──────────────────┘   │   │
│  │         │                  │                   │             │   │
│  │         ▼                  ▼                   ▼             │   │
│  │  ┌──────────────────────────────────────────────────────┐   │   │
│  │  │              LangChain Orchestrator                   │   │   │
│  │  │         (Tools, Agents, Chain Execution)              │   │   │
│  │  └──────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
         │                      │                      │
         ▼                      ▼                      ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  External APIs  │     │   LLM Provider  │     │  Vector Store   │
│  ─────────────  │     │  ─────────────  │     │  ─────────────  │
│  • yfinance     │     │  Configurable:  │     │  Configurable:  │
│  • NewsAPI      │     │  • OpenAI (def) │     │  • Pinecone(def)│
│  • Alpha Vantage│     │  • Anthropic    │     │  • Qdrant       │
│    (optional)   │     │                 │     │  • pgvector     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        FREE              ~$5-10/mo (OpenAI)          FREE
```

---

## 🛠️ Tech Stack (Final)

### Frontend
| Technology | Purpose | Why This Choice |
|------------|---------|-----------------|
| **Next.js 14** | React framework | App Router, SSR, great DX, hot in market |
| **React 18** | UI library | Industry standard, what jobs ask for |
| **TypeScript** | Type safety | Expected for senior roles |
| **Tailwind CSS** | Styling | Rapid prototyping, consistent design |
| **shadcn/ui** | Component library | Beautiful, accessible, customizable |
| **React Query (TanStack)** | Data fetching | Caching, loading states, error handling |
| **Recharts** | Charts | Simple stock price visualization |
| **AWS Amplify** | Hosting | Free tier, AWS on resume, auto-deploy |

### Backend
| Technology | Purpose | Why This Choice |
|------------|---------|-----------------|
| **FastAPI** | API framework | Async-native, auto-docs, Pydantic, hot for AI |
| **Python 3.11+** | Language | AI/ML ecosystem, LangChain/LlamaIndex |
| **Pydantic v2** | Data validation | Type-safe, great error messages |
| **AWS App Runner** | Hosting | Simple container deploy, ~$5-10/mo |
| **cachetools** | In-memory caching | Simple TTL cache, no Redis needed |

### AI/ML Stack
| Technology | Purpose | Why This Choice |
|------------|---------|-----------------|
| **LangChain** | Agent orchestration | Tool use, chains, industry standard |
| **LlamaIndex** | RAG framework | Document indexing, retrieval |
| **OpenAI API** | LLM provider (default) | GPT-4o-mini is cost-effective |
| **Anthropic API** | LLM provider (optional) | Claude 3.5 Haiku as alternative |
| **Pinecone** | Vector store (default) | Free tier, managed, hot in job market |

### Data Sources
| Source | Data Type | Cost |
|--------|-----------|------|
| **yfinance** | Price, volume, fundamentals | Free |
| **NewsAPI** | News headlines | Free tier: 100 req/day |
| **Alpha Vantage** | Technical indicators (optional) | Free tier: 25 req/day |

---

## 💰 Cost Breakdown (Monthly)

| Service | Purpose | Cost |
|---------|---------|------|
| **AWS Amplify** | Frontend hosting | $0 (free tier) |
| **AWS App Runner** | Backend hosting | $5-10 (minimal traffic) |
| **Pinecone** | Vector store | $0 (free tier: 1 index) |
| **OpenAI API** | LLM calls (GPT-4o-mini) | $5-10 |
| **NewsAPI** | News data | $0 (free tier) |
| **Total** | | **~$10-20/month** |

---

## 📁 Project Structure

```
stock-signal-advisor/
├── frontend/                    # Next.js application
│   ├── app/
│   │   ├── page.tsx            # Home page with ticker input
│   │   ├── layout.tsx          # Root layout
│   │   ├── globals.css         # Global styles
│   │   ├── analyze/
│   │   │   └── [ticker]/
│   │   │       └── page.tsx    # Analysis results page
│   │   └── api/                # API routes (optional proxy)
│   ├── components/
│   │   ├── ui/                 # shadcn components
│   │   ├── TickerInput.tsx     # Search/autocomplete
│   │   ├── SignalCard.tsx      # Buy/Hold/Sell display
│   │   ├── SignalBadge.tsx     # Colored signal indicator
│   │   ├── ExplanationPanel.tsx
│   │   ├── SourcesList.tsx
│   │   ├── PriceChart.tsx
│   │   ├── TechnicalIndicators.tsx
│   │   ├── FundamentalsCard.tsx # NEW: Fundamental metrics display
│   │   ├── LoadingState.tsx
│   │   └── Disclaimer.tsx
│   ├── lib/
│   │   ├── api.ts              # API client
│   │   └── utils.ts            # Utility functions
│   ├── hooks/
│   │   └── useAnalysis.ts      # React Query hooks
│   ├── types/
│   │   └── index.ts            # TypeScript types
│   ├── public/
│   │   └── ...                 # Static assets
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   └── next.config.js
│
├── backend/                     # FastAPI application
│   ├── app/
│   │   ├── main.py             # FastAPI app entry point
│   │   ├── config.py           # Settings & environment variables
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── routes/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── analysis.py # POST /analyze endpoint
│   │   │   │   └── health.py   # GET /health endpoint
│   │   │   └── dependencies.py # Dependency injection
│   │   │
│   │   ├── providers/          # NEW: Abstraction layers
│   │   │   ├── __init__.py
│   │   │   ├── llm/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py         # Abstract LLM interface
│   │   │   │   ├── openai.py       # OpenAI implementation
│   │   │   │   ├── anthropic.py    # Anthropic implementation
│   │   │   │   └── factory.py      # Provider factory
│   │   │   └── vectorstore/
│   │   │       ├── __init__.py
│   │   │       ├── base.py         # Abstract vector store interface
│   │   │       ├── pinecone.py     # Pinecone implementation
│   │   │       ├── qdrant.py       # Qdrant implementation (future)
│   │   │       └── factory.py      # Provider factory
│   │   │
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── orchestrator.py # Main agent coordinator
│   │   │   ├── data_agent.py   # Fetches market data
│   │   │   ├── analysis_agent.py # Technical + sentiment analysis
│   │   │   └── tools/
│   │   │       ├── __init__.py
│   │   │       ├── stock_data.py      # yfinance wrapper
│   │   │       ├── news_fetcher.py    # NewsAPI wrapper
│   │   │       ├── technical.py       # RSI, MACD, SMA calculations
│   │   │       ├── fundamentals.py    # NEW: Fundamental analysis
│   │   │       └── sentiment.py       # LLM sentiment analysis
│   │   │
│   │   ├── rag/
│   │   │   ├── __init__.py
│   │   │   ├── indexer.py      # Document indexing (uses vectorstore provider)
│   │   │   ├── retriever.py    # Semantic search (uses vectorstore provider)
│   │   │   └── embeddings.py   # Embedding generation (uses LLM provider)
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── request.py      # Pydantic request models
│   │   │   ├── response.py     # Pydantic response models
│   │   │   └── domain.py       # Domain models (StockData, Fundamentals, etc.)
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   └── cache.py        # In-memory TTL cache
│   │   │
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── helpers.py
│   │
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_analysis.py
│   │   ├── test_agents.py
│   │   ├── test_providers.py   # NEW: Provider abstraction tests
│   │   └── test_tools.py
│   │
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
├── docs/
│   ├── ARCHITECTURE.md         # Detailed architecture docs
│   └── API.md                  # API documentation
│
├── scripts/
│   ├── seed_pinecone.py        # Seed initial embeddings
│   └── test_local.sh           # Local testing script
│
├── docker-compose.yml           # Local development
├── .env.example                 # Environment template
├── .gitignore
├── README.md                    # Project documentation (for GitHub)
└── .github/
    └── workflows/
        └── ci.yml              # GitHub Actions CI
```

---

## 🔄 Provider Abstraction Layers

### LLM Provider Abstraction

This allows swapping between OpenAI and Anthropic (or adding new providers) with a single config change.

```python
# backend/app/providers/llm/base.py
from abc import ABC, abstractmethod
from typing import Optional
from pydantic import BaseModel

class ChatMessage(BaseModel):
    role: str  # "system", "user", "assistant"
    content: str

class LLMResponse(BaseModel):
    content: str
    model: str
    usage: dict  # token counts

class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def complete(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.3,
        max_tokens: int = 1000,
        json_mode: bool = False
    ) -> LLMResponse:
        """Generate a completion from the LLM."""
        pass
    
    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Generate embeddings for text."""
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """Return the model identifier."""
        pass
```

```python
# backend/app/providers/llm/openai.py
from openai import AsyncOpenAI
from .base import LLMProvider, ChatMessage, LLMResponse

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.embedding_model = "text-embedding-3-small"
    
    async def complete(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.3,
        max_tokens: int = 1000,
        json_mode: bool = False
    ) -> LLMResponse:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"} if json_mode else None
        )
        return LLMResponse(
            content=response.choices[0].message.content,
            model=self.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens
            }
        )
    
    async def embed(self, text: str) -> list[float]:
        response = await self.client.embeddings.create(
            model=self.embedding_model,
            input=text
        )
        return response.data[0].embedding
    
    def get_model_name(self) -> str:
        return self.model
```

```python
# backend/app/providers/llm/anthropic.py
from anthropic import AsyncAnthropic
from .base import LLMProvider, ChatMessage, LLMResponse

class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "claude-3-5-haiku-20241022"):
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model
        # Note: Anthropic doesn't have embeddings API, so we fall back to OpenAI
        self._openai_client = None  # Lazy init if needed
    
    async def complete(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.3,
        max_tokens: int = 1000,
        json_mode: bool = False
    ) -> LLMResponse:
        # Extract system message if present
        system = None
        chat_messages = []
        for m in messages:
            if m.role == "system":
                system = m.content
            else:
                chat_messages.append({"role": m.role, "content": m.content})
        
        # Add JSON instruction if needed
        if json_mode and system:
            system += "\n\nRespond with valid JSON only."
        
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=chat_messages
        )
        return LLMResponse(
            content=response.content[0].text,
            model=self.model,
            usage={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens
            }
        )
    
    async def embed(self, text: str) -> list[float]:
        # Anthropic doesn't offer embeddings, fall back to OpenAI
        # In production, you might use a local model or another service
        raise NotImplementedError(
            "Anthropic doesn't provide embeddings. "
            "Configure EMBEDDING_PROVIDER=openai separately."
        )
    
    def get_model_name(self) -> str:
        return self.model
```

```python
# backend/app/providers/llm/factory.py
from .base import LLMProvider
from .openai import OpenAIProvider
from .anthropic import AnthropicProvider
from app.config import settings

def get_llm_provider() -> LLMProvider:
    """Factory function to get the configured LLM provider."""
    
    if settings.LLM_PROVIDER == "openai":
        return OpenAIProvider(
            api_key=settings.OPENAI_API_KEY,
            model=settings.LLM_MODEL or "gpt-4o-mini"
        )
    elif settings.LLM_PROVIDER == "anthropic":
        return AnthropicProvider(
            api_key=settings.ANTHROPIC_API_KEY,
            model=settings.LLM_MODEL or "claude-3-5-haiku-20241022"
        )
    else:
        raise ValueError(f"Unknown LLM provider: {settings.LLM_PROVIDER}")
```

### Vector Store Abstraction

```python
# backend/app/providers/vectorstore/base.py
from abc import ABC, abstractmethod
from typing import Optional
from pydantic import BaseModel

class Document(BaseModel):
    id: str
    content: str
    embedding: Optional[list[float]] = None
    metadata: dict = {}

class SearchResult(BaseModel):
    id: str
    content: str
    score: float
    metadata: dict = {}

class VectorStoreProvider(ABC):
    """Abstract base class for vector store providers."""
    
    @abstractmethod
    async def upsert(self, documents: list[Document]) -> int:
        """Insert or update documents. Returns count of upserted docs."""
        pass
    
    @abstractmethod
    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        filter: Optional[dict] = None
    ) -> list[SearchResult]:
        """Search for similar documents."""
        pass
    
    @abstractmethod
    async def delete(self, ids: list[str]) -> int:
        """Delete documents by ID. Returns count of deleted docs."""
        pass
```

```python
# backend/app/providers/vectorstore/pinecone.py
from pinecone import Pinecone
from .base import VectorStoreProvider, Document, SearchResult

class PineconeProvider(VectorStoreProvider):
    def __init__(self, api_key: str, index_name: str):
        self.pc = Pinecone(api_key=api_key)
        self.index = self.pc.Index(index_name)
    
    async def upsert(self, documents: list[Document]) -> int:
        vectors = [
            {
                "id": doc.id,
                "values": doc.embedding,
                "metadata": {**doc.metadata, "content": doc.content}
            }
            for doc in documents
        ]
        # Pinecone client is sync, but we wrap for interface consistency
        self.index.upsert(vectors=vectors)
        return len(vectors)
    
    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        filter: Optional[dict] = None
    ) -> list[SearchResult]:
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            filter=filter
        )
        return [
            SearchResult(
                id=match["id"],
                content=match["metadata"].get("content", ""),
                score=match["score"],
                metadata=match["metadata"]
            )
            for match in results["matches"]
        ]
    
    async def delete(self, ids: list[str]) -> int:
        self.index.delete(ids=ids)
        return len(ids)
```

```python
# backend/app/providers/vectorstore/factory.py
from .base import VectorStoreProvider
from .pinecone import PineconeProvider
from app.config import settings

def get_vectorstore_provider() -> VectorStoreProvider:
    """Factory function to get the configured vector store provider."""
    
    if settings.VECTORSTORE_PROVIDER == "pinecone":
        return PineconeProvider(
            api_key=settings.PINECONE_API_KEY,
            index_name=settings.PINECONE_INDEX_NAME
        )
    elif settings.VECTORSTORE_PROVIDER == "qdrant":
        # Future implementation
        raise NotImplementedError("Qdrant provider coming soon")
    elif settings.VECTORSTORE_PROVIDER == "pgvector":
        # Future implementation
        raise NotImplementedError("pgvector provider coming soon")
    else:
        raise ValueError(f"Unknown vector store provider: {settings.VECTORSTORE_PROVIDER}")
```

### Using Providers in Application Code

```python
# backend/app/agents/orchestrator.py
from app.providers.llm.factory import get_llm_provider
from app.providers.vectorstore.factory import get_vectorstore_provider

class StockAnalysisOrchestrator:
    def __init__(self):
        self.llm = get_llm_provider()           # Injected based on config
        self.vectorstore = get_vectorstore_provider()  # Injected based on config
    
    async def analyze(self, ticker: str) -> AnalysisResult:
        # Your code uses self.llm and self.vectorstore
        # It doesn't know or care which provider is behind them
        ...
```

---

## 📊 Expanded Fundamental Analysis

### Data Available from yfinance

```python
# backend/app/agents/tools/fundamentals.py
import yfinance as yf
from pydantic import BaseModel
from typing import Optional

class FundamentalMetrics(BaseModel):
    """Comprehensive fundamental analysis metrics."""
    
    # Valuation Metrics
    pe_ratio: Optional[float] = None           # Price to Earnings (TTM)
    forward_pe: Optional[float] = None         # Forward P/E
    peg_ratio: Optional[float] = None          # PEG Ratio (5yr expected)
    price_to_book: Optional[float] = None      # Price to Book
    price_to_sales: Optional[float] = None     # Price to Sales (TTM)
    enterprise_to_ebitda: Optional[float] = None
    
    # Profitability Metrics
    profit_margin: Optional[float] = None      # Net Profit Margin
    operating_margin: Optional[float] = None   # Operating Margin
    gross_margin: Optional[float] = None       # Gross Margin
    return_on_equity: Optional[float] = None   # ROE
    return_on_assets: Optional[float] = None   # ROA
    
    # Growth Metrics
    revenue_growth: Optional[float] = None     # YoY Revenue Growth
    earnings_growth: Optional[float] = None    # YoY Earnings Growth
    earnings_quarterly_growth: Optional[float] = None
    
    # Financial Health
    current_ratio: Optional[float] = None      # Current Assets / Current Liabilities
    debt_to_equity: Optional[float] = None     # Total Debt / Equity
    free_cash_flow: Optional[float] = None     # Free Cash Flow
    operating_cash_flow: Optional[float] = None
    
    # Dividend Info
    dividend_yield: Optional[float] = None
    dividend_payout_ratio: Optional[float] = None
    
    # Size & Market
    market_cap: Optional[float] = None
    enterprise_value: Optional[float] = None
    shares_outstanding: Optional[float] = None
    float_shares: Optional[float] = None
    
    # Analyst Info
    target_mean_price: Optional[float] = None
    target_high_price: Optional[float] = None
    target_low_price: Optional[float] = None
    recommendation_mean: Optional[float] = None  # 1=Buy, 5=Sell
    number_of_analysts: Optional[int] = None


def get_fundamental_metrics(ticker: str) -> FundamentalMetrics:
    """Fetch comprehensive fundamental metrics for a ticker."""
    
    stock = yf.Ticker(ticker)
    info = stock.info
    
    return FundamentalMetrics(
        # Valuation
        pe_ratio=info.get("trailingPE"),
        forward_pe=info.get("forwardPE"),
        peg_ratio=info.get("pegRatio"),
        price_to_book=info.get("priceToBook"),
        price_to_sales=info.get("priceToSalesTrailing12Months"),
        enterprise_to_ebitda=info.get("enterpriseToEbitda"),
        
        # Profitability
        profit_margin=info.get("profitMargins"),
        operating_margin=info.get("operatingMargins"),
        gross_margin=info.get("grossMargins"),
        return_on_equity=info.get("returnOnEquity"),
        return_on_assets=info.get("returnOnAssets"),
        
        # Growth
        revenue_growth=info.get("revenueGrowth"),
        earnings_growth=info.get("earningsGrowth"),
        earnings_quarterly_growth=info.get("earningsQuarterlyGrowth"),
        
        # Financial Health
        current_ratio=info.get("currentRatio"),
        debt_to_equity=info.get("debtToEquity"),
        free_cash_flow=info.get("freeCashflow"),
        operating_cash_flow=info.get("operatingCashflow"),
        
        # Dividends
        dividend_yield=info.get("dividendYield"),
        dividend_payout_ratio=info.get("payoutRatio"),
        
        # Size
        market_cap=info.get("marketCap"),
        enterprise_value=info.get("enterpriseValue"),
        shares_outstanding=info.get("sharesOutstanding"),
        float_shares=info.get("floatShares"),
        
        # Analyst
        target_mean_price=info.get("targetMeanPrice"),
        target_high_price=info.get("targetHighPrice"),
        target_low_price=info.get("targetLowPrice"),
        recommendation_mean=info.get("recommendationMean"),
        number_of_analysts=info.get("numberOfAnalystOpinions")
    )


def interpret_fundamentals(metrics: FundamentalMetrics) -> dict:
    """Interpret fundamental metrics into actionable insights."""
    
    insights = {
        "valuation": [],
        "profitability": [],
        "growth": [],
        "financial_health": [],
        "overall_score": 0  # -1 to 1 scale
    }
    
    score = 0
    factors = 0
    
    # Valuation Analysis
    if metrics.pe_ratio:
        if metrics.pe_ratio < 15:
            insights["valuation"].append("Low P/E ratio suggests undervaluation")
            score += 0.5
        elif metrics.pe_ratio > 30:
            insights["valuation"].append("High P/E ratio suggests premium valuation")
            score -= 0.3
        factors += 1
    
    if metrics.peg_ratio:
        if metrics.peg_ratio < 1:
            insights["valuation"].append("PEG < 1 indicates attractive growth value")
            score += 0.5
        elif metrics.peg_ratio > 2:
            insights["valuation"].append("PEG > 2 suggests expensive relative to growth")
            score -= 0.3
        factors += 1
    
    # Profitability Analysis
    if metrics.profit_margin:
        if metrics.profit_margin > 0.2:
            insights["profitability"].append("Strong profit margins (>20%)")
            score += 0.4
        elif metrics.profit_margin < 0.05:
            insights["profitability"].append("Thin profit margins (<5%)")
            score -= 0.3
        factors += 1
    
    if metrics.return_on_equity:
        if metrics.return_on_equity > 0.15:
            insights["profitability"].append("Excellent ROE (>15%)")
            score += 0.4
        elif metrics.return_on_equity < 0.05:
            insights["profitability"].append("Weak ROE (<5%)")
            score -= 0.3
        factors += 1
    
    # Growth Analysis
    if metrics.revenue_growth:
        if metrics.revenue_growth > 0.15:
            insights["growth"].append("Strong revenue growth (>15% YoY)")
            score += 0.4
        elif metrics.revenue_growth < 0:
            insights["growth"].append("Declining revenue")
            score -= 0.5
        factors += 1
    
    if metrics.earnings_growth:
        if metrics.earnings_growth > 0.2:
            insights["growth"].append("Strong earnings growth (>20% YoY)")
            score += 0.4
        elif metrics.earnings_growth < 0:
            insights["growth"].append("Declining earnings")
            score -= 0.5
        factors += 1
    
    # Financial Health
    if metrics.debt_to_equity:
        if metrics.debt_to_equity < 0.5:
            insights["financial_health"].append("Low debt levels")
            score += 0.3
        elif metrics.debt_to_equity > 2:
            insights["financial_health"].append("High debt burden")
            score -= 0.4
        factors += 1
    
    if metrics.current_ratio:
        if metrics.current_ratio > 1.5:
            insights["financial_health"].append("Strong liquidity position")
            score += 0.2
        elif metrics.current_ratio < 1:
            insights["financial_health"].append("Potential liquidity concerns")
            score -= 0.4
        factors += 1
    
    if metrics.free_cash_flow and metrics.free_cash_flow > 0:
        insights["financial_health"].append("Positive free cash flow")
        score += 0.3
        factors += 1
    
    # Normalize score
    insights["overall_score"] = score / max(factors, 1)
    
    return insights
```

### LangChain Tool Definition for Fundamentals

```python
# Add to backend/app/agents/tools/__init__.py

from langchain.tools import Tool
from .fundamentals import get_fundamental_metrics, interpret_fundamentals

def get_fundamentals_tool():
    def fetch_and_interpret(ticker: str) -> str:
        """Fetch and interpret fundamental metrics for analysis."""
        metrics = get_fundamental_metrics(ticker)
        interpretation = interpret_fundamentals(metrics)
        
        return f"""
        FUNDAMENTAL METRICS FOR {ticker}:
        
        Valuation:
        - P/E Ratio: {metrics.pe_ratio}
        - Forward P/E: {metrics.forward_pe}
        - PEG Ratio: {metrics.peg_ratio}
        - Price/Book: {metrics.price_to_book}
        
        Profitability:
        - Profit Margin: {metrics.profit_margin:.1%} if metrics.profit_margin else 'N/A'
        - Operating Margin: {metrics.operating_margin:.1%} if metrics.operating_margin else 'N/A'
        - ROE: {metrics.return_on_equity:.1%} if metrics.return_on_equity else 'N/A'
        
        Growth:
        - Revenue Growth: {metrics.revenue_growth:.1%} if metrics.revenue_growth else 'N/A'
        - Earnings Growth: {metrics.earnings_growth:.1%} if metrics.earnings_growth else 'N/A'
        
        Financial Health:
        - Debt/Equity: {metrics.debt_to_equity}
        - Current Ratio: {metrics.current_ratio}
        - Free Cash Flow: ${metrics.free_cash_flow:,.0f} if metrics.free_cash_flow else 'N/A'
        
        Analyst Consensus:
        - Target Price: ${metrics.target_mean_price} (Range: ${metrics.target_low_price} - ${metrics.target_high_price})
        - Rating: {metrics.recommendation_mean} (1=Strong Buy, 5=Strong Sell)
        - # of Analysts: {metrics.number_of_analysts}
        
        INSIGHTS:
        - Valuation: {'; '.join(interpretation['valuation']) or 'No strong signals'}
        - Profitability: {'; '.join(interpretation['profitability']) or 'No strong signals'}
        - Growth: {'; '.join(interpretation['growth']) or 'No strong signals'}
        - Financial Health: {'; '.join(interpretation['financial_health']) or 'No strong signals'}
        
        FUNDAMENTAL SCORE: {interpretation['overall_score']:.2f} (-1 bearish to +1 bullish)
        """
    
    return Tool(
        name="get_fundamental_analysis",
        description="Fetch and analyze fundamental metrics (P/E, ROE, growth, debt, etc.) for a stock. Input: ticker symbol (e.g., 'AAPL')",
        func=fetch_and_interpret
    )
```

---

## 🔌 API Design

### Base URL
- **Local:** `http://localhost:8000`
- **Production:** `https://your-app.awsapprunner.com`

### Endpoint: `POST /api/v1/analyze`

Analyzes a stock ticker and returns a Buy/Hold/Sell recommendation.

**Request:**
```json
{
  "ticker": "AAPL",
  "include_news": true,
  "include_technicals": true,
  "include_fundamentals": true
}
```

**Response:**
```json
{
  "ticker": "AAPL",
  "company_name": "Apple Inc.",
  "signal": "HOLD",
  "confidence": 0.72,
  "explanation": "Apple shows mixed signals. Technical indicators are neutral-to-bullish with price above key moving averages. Fundamentals remain strong with high profit margins (25%) and solid ROE (147%), though the P/E of 28 suggests premium valuation. Recent news about iPhone sales in China adds near-term uncertainty. Consider holding current positions.",
  "analysis": {
    "technical": {
      "rsi": 68.4,
      "rsi_interpretation": "Approaching overbought",
      "sma_50": 178.50,
      "sma_200": 165.20,
      "price_vs_sma50": "above",
      "price_vs_sma200": "above",
      "macd_signal": "bullish",
      "volume_trend": "neutral",
      "technical_score": 0.35
    },
    "fundamentals": {
      "pe_ratio": 28.5,
      "forward_pe": 25.2,
      "peg_ratio": 2.1,
      "profit_margin": 0.25,
      "return_on_equity": 1.47,
      "debt_to_equity": 1.87,
      "revenue_growth": 0.02,
      "free_cash_flow": 99200000000,
      "analyst_target": 195.50,
      "analyst_rating": 2.1,
      "fundamental_score": 0.28,
      "insights": [
        "Strong profit margins (>20%)",
        "Excellent ROE (>15%)",
        "PEG > 2 suggests expensive relative to growth"
      ]
    },
    "sentiment": {
      "overall": "mixed",
      "score": 0.15,
      "positive_count": 5,
      "negative_count": 4,
      "neutral_count": 3
    }
  },
  "price_data": {
    "current": 185.50,
    "currency": "USD",
    "change_percent_1d": -1.2,
    "change_percent_1w": 2.5,
    "change_percent_1m": -3.8,
    "high_52w": 199.62,
    "low_52w": 164.08
  },
  "sources": [
    {
      "type": "news",
      "title": "Apple iPhone Sales Drop in China Amid Competition",
      "source": "Reuters",
      "url": "https://reuters.com/...",
      "sentiment": "negative",
      "published_at": "2025-02-14T10:30:00Z"
    }
  ],
  "metadata": {
    "generated_at": "2025-02-15T14:30:00Z",
    "llm_provider": "openai",
    "model_used": "gpt-4o-mini",
    "vectorstore_provider": "pinecone",
    "cached": false
  },
  "disclaimer": "This analysis is for educational purposes only. Not financial advice. Always do your own research."
}
```

### Endpoint: `GET /api/v1/health`

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "providers": {
    "llm": "openai",
    "vectorstore": "pinecone"
  },
  "timestamp": "2025-02-15T14:30:00Z"
}
```

---

## 🤖 Agent Architecture

### Updated Tool List

```python
from langchain.tools import Tool

tools = [
    Tool(
        name="get_stock_price",
        description="Fetch current price, historical prices, and basic info for a stock ticker. Input: ticker symbol (e.g., 'AAPL')",
        func=get_stock_price
    ),
    Tool(
        name="get_news_headlines",
        description="Fetch recent news headlines for a stock ticker. Returns titles, sources, and publication dates. Input: ticker symbol",
        func=get_news_headlines
    ),
    Tool(
        name="calculate_technicals",
        description="Calculate technical indicators (RSI, MACD, SMA) for a stock. Input: ticker symbol",
        func=calculate_technicals
    ),
    Tool(
        name="get_fundamental_analysis",  # NEW
        description="Fetch and analyze fundamental metrics (P/E, ROE, growth, debt, margins, analyst targets) for a stock. Input: ticker symbol",
        func=get_fundamental_analysis
    ),
    Tool(
        name="search_context",
        description="Search for relevant financial context and analysis patterns. Input: natural language query",
        func=search_pinecone_context
    ),
    Tool(
        name="analyze_sentiment",
        description="Analyze sentiment of news headlines. Input: list of headlines as JSON",
        func=analyze_sentiment
    )
]
```

### Updated Analysis Framework

The agent now weighs three pillars:

| Factor | Weight | What It Considers |
|--------|--------|-------------------|
| **Technical Analysis** | 35% | RSI, MACD, moving averages, volume |
| **Fundamental Analysis** | 35% | P/E, growth, margins, debt, analyst targets |
| **Sentiment Analysis** | 30% | News headlines, market mood |

---

## 💬 Updated System Prompt

```python
ANALYSIS_SYSTEM_PROMPT = """
You are a senior financial analyst AI assistant. Your job is to analyze stock data and provide clear, actionable recommendations.

## Your Analysis Framework

1. **Technical Analysis** (35% weight)
   - RSI: <30 oversold (bullish), >70 overbought (bearish)
   - MACD: Crossovers indicate momentum shifts
   - Moving Averages: Price vs 50-day and 200-day SMA
   - Volume: Confirms price movements

2. **Fundamental Analysis** (35% weight)
   - Valuation: P/E, PEG, Price/Book ratios
   - Profitability: Margins, ROE, ROA
   - Growth: Revenue and earnings growth rates
   - Financial Health: Debt/Equity, current ratio, free cash flow
   - Analyst Consensus: Target prices and ratings

3. **Sentiment Analysis** (30% weight)
   - Recent news tone and frequency
   - Market mood indicators
   - Earnings/announcement timing

## Output Requirements

- Provide a clear **BUY**, **HOLD**, or **SELL** signal
- Confidence score (0.0 to 1.0) based on signal strength
- Concise explanation (2-3 paragraphs maximum)
- Cite specific metrics from technical, fundamental, AND sentiment analysis
- Always include caveats about market uncertainty

## Signal Guidelines

- **BUY** (>0.65 confidence): Strong bullish signals across multiple pillars
- **HOLD** (0.35-0.65 confidence): Mixed signals, maintain current position
- **SELL** (<0.35 confidence): Bearish signals, consider reducing exposure

## Critical Rules

- NEVER guarantee returns or predict specific price targets
- Always balance short-term technicals with long-term fundamentals
- Consider whether valuation metrics are appropriate for the company type
  (e.g., high-growth tech vs. mature dividend stocks)
- Always recommend users do their own research
- If data is insufficient for any pillar, say so clearly
"""
```

---

## 🔐 Environment Variables

```bash
# .env.example

# ===================
# LLM Provider Config
# ===================
LLM_PROVIDER=openai                    # openai | anthropic
LLM_MODEL=gpt-4o-mini                  # or claude-3-5-haiku-20241022

# OpenAI (required if LLM_PROVIDER=openai)
OPENAI_API_KEY=sk-...

# Anthropic (required if LLM_PROVIDER=anthropic)
ANTHROPIC_API_KEY=sk-ant-...

# ===================
# Vector Store Config
# ===================
VECTORSTORE_PROVIDER=pinecone          # pinecone | qdrant | pgvector

# Pinecone (required if VECTORSTORE_PROVIDER=pinecone)
PINECONE_API_KEY=...
PINECONE_INDEX_NAME=stock-signal-advisor

# Qdrant (required if VECTORSTORE_PROVIDER=qdrant)
# QDRANT_URL=http://localhost:6333
# QDRANT_API_KEY=...

# ===================
# Data Source API Keys
# ===================
NEWS_API_KEY=...

# ===================
# App Configuration
# ===================
CACHE_TTL_SECONDS=3600
LOG_LEVEL=INFO
ENVIRONMENT=development

# ===================
# Frontend (Next.js)
# ===================
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 🗓️ Updated Development Roadmap (2-3 Weeks)

### Week 1: Foundation & Abstractions

| Day | Tasks | Deliverables |
|-----|-------|--------------|
| **1** | Project setup | GitHub repo, folder structure, Docker setup |
| **2** | Provider abstractions | LLM base class, VectorStore base class |
| **3** | OpenAI + Pinecone providers | Working implementations with tests |
| **4** | Backend scaffold | FastAPI app, health endpoint, Pydantic models |
| **5** | Stock data + technicals | yfinance wrapper, RSI/MACD/SMA calculations |
| **6** | Fundamentals tool | Full fundamental metrics + interpretation |
| **7** | News integration | NewsAPI wrapper, headline fetching |

### Week 2: AI Integration

| Day | Tasks | Deliverables |
|-----|-------|--------------|
| **8** | LLM integration | Complete calls via abstraction layer |
| **9** | Pinecone setup | Index creation, embedding pipeline |
| **10** | RAG implementation | Document indexing, retrieval (via abstraction) |
| **11** | LangChain agent | Tool definitions including fundamentals |
| **12** | Orchestrator | Full analysis pipeline, caching |
| **13** | Frontend setup | Next.js app, Tailwind, shadcn/ui |
| **14** | Core UI | Ticker input, signal card, explanation panel |

### Week 3: Polish & Deploy

| Day | Tasks | Deliverables |
|-----|-------|--------------|
| **15** | Fundamentals UI | FundamentalsCard component |
| **16** | Error handling | Edge cases, graceful failures |
| **17** | Testing | Unit tests, integration tests, provider tests |
| **18** | AWS setup | App Runner config, Amplify setup |
| **19** | Deployment | CI/CD pipeline, environment variables |
| **20-21** | Documentation + Demo | README, pre-cache tickers, final polish |

---

## 🧪 Testing Strategy

### Provider Abstraction Tests

```python
# tests/test_providers.py
import pytest
from app.providers.llm.base import LLMProvider, ChatMessage
from app.providers.llm.openai import OpenAIProvider
from app.providers.vectorstore.base import VectorStoreProvider, Document
from app.providers.vectorstore.pinecone import PineconeProvider

class TestLLMProviders:
    @pytest.mark.asyncio
    async def test_openai_complete(self, openai_provider: OpenAIProvider):
        messages = [ChatMessage(role="user", content="Say hello")]
        response = await openai_provider.complete(messages)
        assert response.content
        assert response.model == "gpt-4o-mini"
    
    @pytest.mark.asyncio
    async def test_openai_embed(self, openai_provider: OpenAIProvider):
        embedding = await openai_provider.embed("test text")
        assert len(embedding) == 1536  # OpenAI embedding dimension
    
    def test_provider_interface_compliance(self):
        # Ensure all providers implement the interface
        assert issubclass(OpenAIProvider, LLMProvider)

class TestVectorStoreProviders:
    @pytest.mark.asyncio
    async def test_pinecone_upsert_search(self, pinecone_provider: PineconeProvider):
        doc = Document(
            id="test-1",
            content="Test content",
            embedding=[0.1] * 1536,
            metadata={"type": "test"}
        )
        await pinecone_provider.upsert([doc])
        results = await pinecone_provider.search([0.1] * 1536, top_k=1)
        assert len(results) == 1
        assert results[0].id == "test-1"
```

---

## 📊 Interview Talking Points (Updated)

- "I built **provider-agnostic abstractions** — swapping OpenAI for Claude or Pinecone for Qdrant is a one-line config change"
- "The agent combines **three analysis pillars**: technicals, fundamentals, and sentiment — each weighted in the final recommendation"
- "**Fundamental analysis** includes 20+ metrics: valuation ratios, profitability, growth, and financial health indicators"
- "**LangChain agent** autonomously decides which tools to call based on the analysis needed"
- "The architecture is **SaaS-ready** — adding auth and subscriptions would take 2-3 weeks, not a rewrite"

---

## 🚀 Future Enhancements (Post-MVP)

| Feature | Complexity | Value |
|---------|------------|-------|
| Anthropic provider implementation | Low | Flexibility |
| Qdrant/pgvector providers | Medium | Self-hosting option |
| User authentication | Medium | SaaS enablement |
| Stripe subscriptions | Medium | Monetization |
| Chart pattern analysis (vision) | Medium | Cooler demo |
| SEC filings RAG (10-K, 10-Q) | High | Deeper fundamentals |
| Portfolio analysis | High | Premium feature |

---

## 📚 Resources & References

### Documentation
- [LangChain Agents](https://python.langchain.com/docs/modules/agents/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Next.js App Router](https://nextjs.org/docs/app)
- [Pinecone](https://docs.pinecone.io/)
- [Qdrant](https://qdrant.tech/documentation/)
- [yfinance](https://github.com/ranaroussi/yfinance)
- [AWS App Runner](https://docs.aws.amazon.com/apprunner/)
- [AWS Amplify](https://docs.amplify.aws/)

---

## 🤝 Author Context

**Rafael Hocevar** — Principal Software Engineer

### Relevant Experience
- **VybeOS (Current):** Building AI-powered SaaS with RAG, LlamaIndex, pgvector, and model-agnostic LLM providers (Vertex AI, OpenAI, Anthropic)
- **Blizzard Entertainment:** Distributed systems for Warcraft Rumble (150K+ DAU), microservices architecture
- **Kabam/MGN Studios:** Full-stack game development, real-time systems

### Skills Demonstrated by This Project
- ✅ AI/ML Integration (RAG, agents, LLM orchestration)
- ✅ Provider abstraction patterns (swappable LLM & vector stores)
- ✅ Full-stack development (React/Next.js, FastAPI)
- ✅ Cloud infrastructure (AWS App Runner, Amplify)
- ✅ API design (REST, Pydantic)
- ✅ Production patterns (caching, error handling)

---

*Last updated: February 2025*
*Version: 3.0 (With Abstractions & Expanded Fundamentals)*
