# API Reference

Base URLs:
- **Local:** `http://localhost:8000`
- **Production:** `https://xdvpqzqg4m.us-east-2.awsapprunner.com`
- **Interactive docs (Swagger):** `http://localhost:8000/docs` (local only — disabled in production)

All endpoints use the `/api/v1/` prefix. Responses are JSON.

---

## Health

### `GET /api/v1/health`

Returns service status and active provider configuration.

**Response `200`**

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "providers": {
    "llm": "openai",
    "vectorstore": "pinecone"
  },
  "timestamp": "2026-02-21T18:00:00.000000Z"
}
```

**Example**
```bash
curl https://xdvpqzqg4m.us-east-2.awsapprunner.com/api/v1/health
```

---

## Analysis

### `POST /api/v1/signal`

Runs the full three-pillar analysis (technical + fundamental + sentiment) for a stock ticker. Results are cached for 1 hour (keyed by ticker).

**Request body**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ticker` | string | Yes | Stock ticker symbol (1–10 chars, e.g. `AAPL`) |
| `include_technicals` | boolean | No | Include technical pillar (default: `true`) |
| `include_fundamentals` | boolean | No | Include fundamental pillar (default: `true`) |
| `include_news` | boolean | No | Include news/sentiment pillar (default: `true`) |

**Example request**
```bash
curl -X POST https://xdvpqzqg4m.us-east-2.awsapprunner.com/api/v1/signal \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL"}'
```

**Response `200`**

```json
{
  "ticker": "AAPL",
  "company_name": "Apple Inc.",
  "signal": "BUY",
  "confidence": 0.72,
  "explanation": "Apple shows strong technical momentum with RSI at 58 (neutral-bullish) and price above both 50-day and 200-day moving averages...",
  "analysis": {
    "technical": {
      "rsi": 58.3,
      "rsi_interpretation": "Neutral",
      "sma_50": 225.40,
      "sma_200": 210.15,
      "price_vs_sma50": "ABOVE",
      "price_vs_sma200": "ABOVE",
      "macd_signal": "BULLISH",
      "volume_trend": "INCREASING",
      "technical_score": 0.68
    },
    "fundamentals": {
      "pe_ratio": 32.1,
      "forward_pe": 28.5,
      "peg_ratio": 2.1,
      "price_to_book": 48.2,
      "profit_margin": 0.263,
      "return_on_equity": 1.47,
      "revenue_growth": 0.051,
      "earnings_growth": 0.107,
      "debt_to_equity": 1.45,
      "dividend_yield": 0.0044,
      "market_cap": 3450000000000,
      "analyst_target": 245.0,
      "analyst_rating": 1.8,
      "number_of_analysts": 42,
      "fundamental_score": 0.71,
      "insights": ["Trading above analyst consensus target", "Strong profit margins above 25%"]
    },
    "sentiment": {
      "overall": "POSITIVE",
      "score": 0.75,
      "positive_count": 6,
      "negative_count": 1,
      "neutral_count": 3
    }
  },
  "price_data": {
    "current": 229.87,
    "currency": "USD",
    "change_percent_1d": 1.23,
    "change_percent_1w": 2.45,
    "change_percent_1m": -3.12,
    "high_52w": 260.10,
    "low_52w": 164.08,
    "price_history": [
      {"date": "2026-01-22", "close": 227.50},
      {"date": "2026-01-23", "close": 229.87}
    ]
  },
  "sources": [
    {
      "type": "news",
      "title": "Apple Reports Record Quarter",
      "source": "Reuters",
      "url": "https://reuters.com/...",
      "sentiment": "POSITIVE",
      "published_at": "2026-02-20T14:30:00Z"
    }
  ],
  "metadata": {
    "generated_at": "2026-02-21T18:00:00Z",
    "llm_provider": "openai",
    "model_used": "gpt-4o-mini",
    "vectorstore_provider": "pinecone",
    "cached": false
  }
}
```

**Signal values:** `BUY` | `HOLD` | `SELL`

**Confidence:** float from `0.0` to `1.0` — weighted average of pillar scores, dynamically reweighted based on which pillars are available.

**Error responses**

| Status | Condition |
|--------|-----------|
| `404` | Ticker not found or has no data in yfinance |
| `429` | LLM provider rate limit exceeded |
| `502` | Upstream data or AI provider error |

---

## Tools

Individual tool endpoints are provided for debugging and exploration. They expose the same data-gathering functions used internally by the analysis pipeline.

---

### `GET /api/v1/tools/stock-price/{ticker}`

Returns current price data, 52-week range, and 30-day price history.

**Path parameter:** `ticker` — stock symbol (1–10 alphanumeric chars)

**Example**
```bash
curl http://localhost:8000/api/v1/tools/stock-price/AAPL
```

**Response `200`**
```json
{
  "current": 229.87,
  "currency": "USD",
  "change_percent_1d": 1.23,
  "change_percent_1w": 2.45,
  "change_percent_1m": -3.12,
  "high_52w": 260.10,
  "low_52w": 164.08,
  "price_history": [
    {"date": "2026-01-22", "close": 227.50}
  ]
}
```

---

### `GET /api/v1/tools/company-name/{ticker}`

Resolves a ticker to its company name.

**Example**
```bash
curl http://localhost:8000/api/v1/tools/company-name/MSFT
```

**Response `200`**
```json
{
  "ticker": "MSFT",
  "company_name": "Microsoft Corporation"
}
```

---

### `GET /api/v1/tools/technicals/{ticker}`

Calculates RSI, moving averages, MACD signal, and volume trend.

**Example**
```bash
curl http://localhost:8000/api/v1/tools/technicals/NVDA
```

**Response `200`**
```json
{
  "rsi": 62.1,
  "rsi_interpretation": "Neutral-Bullish",
  "sma_50": 138.20,
  "sma_200": 115.40,
  "price_vs_sma50": "ABOVE",
  "price_vs_sma200": "ABOVE",
  "macd_signal": "BULLISH",
  "volume_trend": "INCREASING",
  "technical_score": 0.74
}
```

**`price_vs_sma50` / `price_vs_sma200` values:** `ABOVE` | `BELOW`
**`macd_signal` values:** `BULLISH` | `BEARISH` | `NEUTRAL`
**`volume_trend` values:** `INCREASING` | `DECREASING` | `NEUTRAL`
**`technical_score`:** 0.0 (bearish) to 1.0 (bullish)

---

### `GET /api/v1/tools/fundamentals/{ticker}`

Returns valuation ratios, profitability metrics, growth rates, and analyst targets.

**Example**
```bash
curl http://localhost:8000/api/v1/tools/fundamentals/GOOGL
```

**Response `200`** *(all fields nullable — availability depends on yfinance data)*
```json
{
  "pe_ratio": 22.4,
  "forward_pe": 19.8,
  "peg_ratio": 1.3,
  "price_to_book": 6.1,
  "price_to_sales": 6.0,
  "enterprise_to_ebitda": 14.2,
  "profit_margin": 0.238,
  "operating_margin": 0.280,
  "gross_margin": 0.564,
  "return_on_equity": 0.311,
  "return_on_assets": 0.128,
  "revenue_growth": 0.123,
  "earnings_growth": 0.312,
  "earnings_quarterly_growth": 0.285,
  "current_ratio": 1.84,
  "debt_to_equity": 0.07,
  "free_cash_flow": 72500000000,
  "dividend_yield": null,
  "market_cap": 2150000000000,
  "analyst_target": 210.0,
  "analyst_rating": 1.7,
  "number_of_analysts": 58,
  "fundamental_score": 0.78,
  "insights": ["Revenue growth above 10% YoY", "Low debt-to-equity ratio"]
}
```

---

### `GET /api/v1/tools/news/{ticker}`

Fetches recent news headlines for a ticker from NewsAPI.

**Example**
```bash
curl http://localhost:8000/api/v1/tools/news/TSLA
```

**Response `200`**
```json
[
  {
    "type": "news",
    "title": "Tesla Delivers Record Vehicles in Q4",
    "source": "Bloomberg",
    "url": "https://bloomberg.com/...",
    "sentiment": null,
    "published_at": "2026-02-20T10:00:00Z"
  }
]
```

---

### `GET /api/v1/tools/sentiment/{ticker}`

Fetches news headlines and classifies their sentiment using the LLM.

**Example**
```bash
curl http://localhost:8000/api/v1/tools/sentiment/TSLA
```

**Response `200`**
```json
{
  "overall": "NEGATIVE",
  "score": 0.31,
  "positive_count": 1,
  "negative_count": 4,
  "neutral_count": 2
}
```

**`overall` values:** `POSITIVE` | `NEGATIVE` | `NEUTRAL` | `MIXED`
**`score`:** 0.0 (very negative) to 1.0 (very positive)

---

### `GET /api/v1/tools/rag-search`

Performs semantic search over the financial knowledge vector store.

**Query parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | Natural language query |
| `top_k` | integer | No | Max results (1–20, default: 5) |

**Example**
```bash
curl "http://localhost:8000/api/v1/tools/rag-search?query=RSI+oversold+signal&top_k=3"
```

**Response `200`**
```json
[
  {
    "id": "tech-rsi-001",
    "content": "RSI below 30 indicates an oversold condition, suggesting potential buying opportunity...",
    "metadata": {"category": "technical_analysis"},
    "score": 0.92
  }
]
```

---

## Error Format

All errors return a JSON body with a `detail` field:

```json
{
  "detail": "Ticker \"XYZINVALID\" not found or has no market data."
}
```
