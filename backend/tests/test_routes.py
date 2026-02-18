"""Tests for API route endpoints."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.enums import MacdSignal, SentimentType, SignalType, TrendDirection, VolumeTrend
from app.main import app
from app.providers.llm.base import LLMRateLimitError
from app.providers.vectorstore.base import SearchResult
from app.models.domain import (
    AnalysisMetadata,
    AnalysisResult,
    FundamentalAnalysis,
    NewsSource,
    PriceData,
    SentimentAnalysis,
    TechnicalAnalysis,
)
from app.models.response import AnalyzeResponse

client = TestClient(app)


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------


class TestHealthEndpoint:
    def test_health_returns_200(self):
        response = client.get("/api/v1/health")
        assert response.status_code == 200

    def test_health_response_structure(self):
        data = client.get("/api/v1/health").json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"
        assert "providers" in data
        assert "timestamp" in data

    def test_health_providers_populated(self):
        data = client.get("/api/v1/health").json()
        assert data["providers"]["llm"] is not None
        assert data["providers"]["vectorstore"] is not None


# ---------------------------------------------------------------------------
# Analysis endpoint
# ---------------------------------------------------------------------------

_SAMPLE_ANALYZE_RESPONSE = AnalyzeResponse(
    ticker="AAPL",
    company_name="Apple Inc.",
    signal=SignalType.BUY,
    confidence=0.75,
    explanation="Strong outlook.",
    analysis=AnalysisResult(),
    metadata=AnalysisMetadata(
        generated_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        llm_provider="openai",
        model_used="gpt-4o-mini",
        vectorstore_provider="pinecone",
    ),
)


class TestAnalyzeEndpoint:
    @patch(
        "app.api.routes.analysis._orchestrator.analyze",
        new_callable=AsyncMock,
        return_value=_SAMPLE_ANALYZE_RESPONSE,
    )
    def test_analyze_returns_200(self, mock_analyze):
        response = client.post("/api/v1/analyze", json={"ticker": "AAPL"})
        assert response.status_code == 200

    @patch(
        "app.api.routes.analysis._orchestrator.analyze",
        new_callable=AsyncMock,
        return_value=_SAMPLE_ANALYZE_RESPONSE,
    )
    def test_analyze_response_structure(self, mock_analyze):
        data = client.post("/api/v1/analyze", json={"ticker": "AAPL"}).json()
        assert data["ticker"] == "AAPL"
        assert data["signal"] == SignalType.BUY.value
        assert data["confidence"] == 0.75
        assert "explanation" in data
        assert "analysis" in data
        assert "metadata" in data

    @patch(
        "app.api.routes.analysis._orchestrator.analyze",
        new_callable=AsyncMock,
        return_value=_SAMPLE_ANALYZE_RESPONSE,
    )
    def test_analyze_calls_orchestrator(self, mock_analyze):
        client.post("/api/v1/analyze", json={"ticker": "aapl"})
        mock_analyze.assert_called_once()

    def test_analyze_missing_ticker(self):
        response = client.post("/api/v1/analyze", json={})
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Tools: stock-price
# ---------------------------------------------------------------------------

_SAMPLE_PRICE = PriceData(
    current=150.0,
    change_percent_1d=-1.5,
    change_percent_1w=2.3,
    change_percent_1m=5.0,
)


class TestStockPriceEndpoint:
    @patch("app.api.routes.tools.get_stock_price", return_value=_SAMPLE_PRICE)
    @patch("app.api.routes.tools.get_ticker")
    def test_returns_price_data(self, mock_get_ticker, mock_fn):
        response = client.get("/api/v1/tools/stock-price/AAPL")
        assert response.status_code == 200
        data = response.json()
        assert data["current"] == 150.0
        assert data["change_percent_1d"] == -1.5

    @patch("app.api.routes.tools.get_stock_price", side_effect=ValueError("No data"))
    @patch("app.api.routes.tools.get_ticker")
    def test_returns_404_on_value_error(self, mock_get_ticker, mock_fn):
        response = client.get("/api/v1/tools/stock-price/INVALID")
        assert response.status_code == 404

    @patch("app.api.routes.tools.get_stock_price", side_effect=RuntimeError("boom"))
    @patch("app.api.routes.tools.get_ticker")
    def test_returns_502_on_unexpected_error(self, mock_get_ticker, mock_fn):
        response = client.get("/api/v1/tools/stock-price/AAPL")
        assert response.status_code == 502
        assert response.json()["detail"] == "Upstream data provider error"

    def test_rejects_invalid_ticker(self):
        response = client.get("/api/v1/tools/stock-price/INVALID!!!")
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Tools: company-name
# ---------------------------------------------------------------------------


class TestCompanyNameEndpoint:
    @patch("app.api.routes.tools.get_company_name", return_value="Apple Inc.")
    @patch("app.api.routes.tools.get_ticker")
    def test_returns_company_name(self, mock_get_ticker, mock_fn):
        response = client.get("/api/v1/tools/company-name/AAPL")
        assert response.status_code == 200
        data = response.json()
        assert data["ticker"] == "AAPL"
        assert data["company_name"] == "Apple Inc."

    @patch("app.api.routes.tools.get_company_name", return_value=None)
    @patch("app.api.routes.tools.get_ticker")
    def test_returns_null_when_unknown(self, mock_get_ticker, mock_fn):
        response = client.get("/api/v1/tools/company-name/XYZ")
        assert response.status_code == 200
        assert response.json()["company_name"] is None

    @patch("app.api.routes.tools.get_company_name", side_effect=RuntimeError("boom"))
    @patch("app.api.routes.tools.get_ticker")
    def test_returns_502_on_error(self, mock_get_ticker, mock_fn):
        response = client.get("/api/v1/tools/company-name/AAPL")
        assert response.status_code == 502


# ---------------------------------------------------------------------------
# Tools: technicals
# ---------------------------------------------------------------------------

_SAMPLE_TECHNICALS = TechnicalAnalysis(
    rsi=55.0,
    rsi_interpretation="neutral",
    sma_50=145.0,
    sma_200=130.0,
    price_vs_sma50=TrendDirection.ABOVE,
    price_vs_sma200=TrendDirection.ABOVE,
    macd_signal=MacdSignal.BULLISH,
    volume_trend=VolumeTrend.NEUTRAL,
    technical_score=0.75,
)


class TestTechnicalsEndpoint:
    @patch("app.api.routes.tools.calculate_technicals", return_value=_SAMPLE_TECHNICALS)
    @patch("app.api.routes.tools.get_ticker")
    def test_returns_technicals(self, mock_get_ticker, mock_fn):
        response = client.get("/api/v1/tools/technicals/AAPL")
        assert response.status_code == 200
        data = response.json()
        assert data["rsi"] == 55.0
        assert data["technical_score"] == 0.75

    @patch("app.api.routes.tools.calculate_technicals", side_effect=ValueError("No data"))
    @patch("app.api.routes.tools.get_ticker")
    def test_returns_404_on_value_error(self, mock_get_ticker, mock_fn):
        response = client.get("/api/v1/tools/technicals/INVALID")
        assert response.status_code == 404

    @patch("app.api.routes.tools.calculate_technicals", side_effect=RuntimeError("boom"))
    @patch("app.api.routes.tools.get_ticker")
    def test_returns_502_on_unexpected_error(self, mock_get_ticker, mock_fn):
        response = client.get("/api/v1/tools/technicals/AAPL")
        assert response.status_code == 502


# ---------------------------------------------------------------------------
# Tools: fundamentals
# ---------------------------------------------------------------------------

_SAMPLE_FUNDAMENTALS = FundamentalAnalysis(
    pe_ratio=25.0,
    market_cap=2_500_000_000_000,
    fundamental_score=0.65,
)


class TestFundamentalsEndpoint:
    @patch(
        "app.api.routes.tools.calculate_fundamentals",
        return_value=_SAMPLE_FUNDAMENTALS,
    )
    @patch("app.api.routes.tools.get_ticker")
    def test_returns_fundamentals(self, mock_get_ticker, mock_fn):
        response = client.get("/api/v1/tools/fundamentals/AAPL")
        assert response.status_code == 200
        data = response.json()
        assert data["pe_ratio"] == 25.0
        assert data["fundamental_score"] == 0.65

    @patch(
        "app.api.routes.tools.calculate_fundamentals",
        side_effect=ValueError("No data"),
    )
    @patch("app.api.routes.tools.get_ticker")
    def test_returns_404_on_value_error(self, mock_get_ticker, mock_fn):
        response = client.get("/api/v1/tools/fundamentals/INVALID")
        assert response.status_code == 404

    @patch(
        "app.api.routes.tools.calculate_fundamentals",
        side_effect=RuntimeError("boom"),
    )
    @patch("app.api.routes.tools.get_ticker")
    def test_returns_502_on_unexpected_error(self, mock_get_ticker, mock_fn):
        response = client.get("/api/v1/tools/fundamentals/AAPL")
        assert response.status_code == 502


# ---------------------------------------------------------------------------
# Tools: news
# ---------------------------------------------------------------------------

_SAMPLE_NEWS = [
    NewsSource(
        title="Apple Reports Record Revenue",
        source="Reuters",
        url="https://example.com/1",
        published_at=datetime(2025, 2, 14, tzinfo=timezone.utc),
    ),
    NewsSource(
        title="iPhone Sales Decline in China",
        source="Bloomberg",
        url="https://example.com/2",
        published_at=datetime(2025, 2, 13, tzinfo=timezone.utc),
    ),
]


class TestNewsEndpoint:
    @patch("app.api.routes.tools.fetch_news_headlines", return_value=_SAMPLE_NEWS)
    def test_returns_news(self, mock_fn):
        response = client.get("/api/v1/tools/news/AAPL")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["title"] == "Apple Reports Record Revenue"
        assert data[0]["source"] == "Reuters"

    @patch("app.api.routes.tools.fetch_news_headlines", return_value=[])
    def test_returns_empty_list(self, mock_fn):
        response = client.get("/api/v1/tools/news/AAPL")
        assert response.status_code == 200
        assert response.json() == []

    @patch(
        "app.api.routes.tools.fetch_news_headlines",
        side_effect=ValueError("NEWS_API_KEY is not configured"),
    )
    def test_returns_400_on_value_error(self, mock_fn):
        response = client.get("/api/v1/tools/news/AAPL")
        assert response.status_code == 400

    @patch(
        "app.api.routes.tools.fetch_news_headlines",
        side_effect=RuntimeError("boom"),
    )
    def test_returns_502_on_unexpected_error(self, mock_fn):
        response = client.get("/api/v1/tools/news/AAPL")
        assert response.status_code == 502


# ---------------------------------------------------------------------------
# Tools: sentiment
# ---------------------------------------------------------------------------

_SAMPLE_SENTIMENT = SentimentAnalysis(
    overall=SentimentType.MIXED,
    score=0.55,
    positive_count=1,
    negative_count=1,
    neutral_count=0,
)


class TestSentimentEndpoint:
    @patch(
        "app.api.routes.tools.analyze_sentiment",
        new_callable=AsyncMock,
        return_value=_SAMPLE_SENTIMENT,
    )
    @patch("app.api.routes.tools.fetch_news_headlines", return_value=_SAMPLE_NEWS)
    def test_returns_sentiment(self, mock_news, mock_sentiment):
        response = client.get("/api/v1/tools/sentiment/AAPL")
        assert response.status_code == 200
        data = response.json()
        assert data["overall"] == "mixed"
        assert data["score"] == 0.55
        assert data["positive_count"] == 1
        assert data["negative_count"] == 1
        mock_news.assert_called_once_with("AAPL")
        mock_sentiment.assert_called_once_with(_SAMPLE_NEWS)

    @patch(
        "app.api.routes.tools.fetch_news_headlines",
        side_effect=ValueError("NEWS_API_KEY is not configured"),
    )
    def test_returns_400_on_value_error(self, mock_fn):
        response = client.get("/api/v1/tools/sentiment/AAPL")
        assert response.status_code == 400

    @patch(
        "app.api.routes.tools.fetch_news_headlines",
        side_effect=RuntimeError("boom"),
    )
    def test_returns_502_on_unexpected_error(self, mock_fn):
        response = client.get("/api/v1/tools/sentiment/AAPL")
        assert response.status_code == 502

    @patch(
        "app.api.routes.tools.analyze_sentiment",
        new_callable=AsyncMock,
        side_effect=LLMRateLimitError("rate limit exceeded"),
    )
    @patch("app.api.routes.tools.fetch_news_headlines", return_value=_SAMPLE_NEWS)
    def test_returns_429_on_rate_limit(self, mock_news, mock_sentiment):
        response = client.get("/api/v1/tools/sentiment/AAPL")
        assert response.status_code == 429
        assert "rate limit" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Tools: rag-search
# ---------------------------------------------------------------------------

_SAMPLE_SEARCH_RESULTS = [
    SearchResult(
        id="ta-rsi-oversold",
        content="When RSI drops below 30, the stock is oversold.",
        score=0.92,
        metadata={"doc_type": "analysis"},
    ),
    SearchResult(
        id="fa-pe-ratio",
        content="P/E ratio measures how much investors pay per dollar of earnings.",
        score=0.85,
        metadata={"doc_type": "analysis"},
    ),
]


class TestRagSearchEndpoint:
    @patch(
        "app.api.routes.tools.retrieve",
        new_callable=AsyncMock,
        return_value=_SAMPLE_SEARCH_RESULTS,
    )
    def test_returns_search_results(self, mock_retrieve):
        response = client.get("/api/v1/tools/rag-search?query=RSI+oversold")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["id"] == "ta-rsi-oversold"
        assert data[0]["score"] == 0.92
        assert data[0]["content"] == "When RSI drops below 30, the stock is oversold."
        mock_retrieve.assert_called_once_with("RSI oversold", top_k=5)

    @patch(
        "app.api.routes.tools.retrieve",
        new_callable=AsyncMock,
        return_value=[],
    )
    def test_returns_empty_list(self, mock_retrieve):
        response = client.get("/api/v1/tools/rag-search?query=obscure+query")
        assert response.status_code == 200
        assert response.json() == []

    @patch(
        "app.api.routes.tools.retrieve",
        new_callable=AsyncMock,
        return_value=_SAMPLE_SEARCH_RESULTS[:1],
    )
    def test_passes_top_k_parameter(self, mock_retrieve):
        response = client.get("/api/v1/tools/rag-search?query=RSI&top_k=3")
        assert response.status_code == 200
        mock_retrieve.assert_called_once_with("RSI", top_k=3)

    def test_rejects_missing_query(self):
        response = client.get("/api/v1/tools/rag-search")
        assert response.status_code == 422

    @patch(
        "app.api.routes.tools.retrieve",
        new_callable=AsyncMock,
        side_effect=LLMRateLimitError("rate limit"),
    )
    def test_returns_429_on_rate_limit(self, mock_retrieve):
        response = client.get("/api/v1/tools/rag-search?query=test")
        assert response.status_code == 429

    @patch(
        "app.api.routes.tools.retrieve",
        new_callable=AsyncMock,
        side_effect=RuntimeError("boom"),
    )
    def test_returns_502_on_unexpected_error(self, mock_retrieve):
        response = client.get("/api/v1/tools/rag-search?query=test")
        assert response.status_code == 502


# ---------------------------------------------------------------------------
# Ticker validation (shared across all tools endpoints)
# ---------------------------------------------------------------------------


class TestTickerValidation:
    """Verify the ticker regex pattern rejects invalid symbols."""

    @pytest.mark.parametrize(
        "endpoint",
        [
            "/api/v1/tools/stock-price/",
            "/api/v1/tools/company-name/",
            "/api/v1/tools/technicals/",
            "/api/v1/tools/fundamentals/",
            "/api/v1/tools/news/",
            "/api/v1/tools/sentiment/",
        ],
    )
    @pytest.mark.parametrize("bad_ticker", ["AB CD", "A@#$", "VERYLONGTICKER1"])
    def test_rejects_invalid_tickers(self, endpoint, bad_ticker):
        response = client.get(f"{endpoint}{bad_ticker}")
        assert response.status_code == 422
