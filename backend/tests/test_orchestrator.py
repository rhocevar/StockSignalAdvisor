"""Tests for the StockAnalysisOrchestrator."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.enums import SentimentType, SignalType
from app.models.domain import (
    AgentResult,
    FundamentalAnalysis,
    NewsSource,
    PriceData,
    SentimentAnalysis,
    TechnicalAnalysis,
)
from app.models.request import AnalyzeRequest
from app.agents.orchestrator import StockAnalysisOrchestrator, _compute_weighted_confidence
from app.services.cache import clear_cache


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _clear_cache():
    """Ensure cache is empty before each test."""
    clear_cache()
    yield
    clear_cache()


@pytest.fixture
def sample_price():
    return PriceData(current=150.0, change_percent_1d=1.2)


@pytest.fixture
def sample_technicals():
    return TechnicalAnalysis(rsi=55.0, technical_score=0.70)


@pytest.fixture
def sample_fundamentals():
    return FundamentalAnalysis(pe_ratio=25.0, fundamental_score=0.60)


@pytest.fixture
def sample_headlines():
    return [
        NewsSource(title="Good news", source="Reuters"),
        NewsSource(title="Bad news", source="Bloomberg"),
    ]


@pytest.fixture
def sample_sentiment():
    return SentimentAnalysis(
        overall=SentimentType.MIXED, score=0.55, positive_count=1, negative_count=1
    )


@pytest.fixture
def sample_agent_result():
    return AgentResult(signal=SignalType.BUY, confidence=0.85, explanation="Strong outlook.")


def _patch_all(
    price=None,
    technicals=None,
    fundamentals=None,
    headlines=None,
    sentiment=None,
    agent_result=None,
    company_name="Apple Inc.",
):
    """Return a dict of patch context managers for all orchestrator dependencies."""
    return {
        "get_ticker": patch(
            "app.agents.orchestrator.get_ticker", return_value=MagicMock()
        ),
        "get_stock_price": patch(
            "app.agents.orchestrator.get_stock_price", return_value=price
        ),
        "get_company_name": patch(
            "app.agents.orchestrator.get_company_name", return_value=company_name
        ),
        "calculate_technicals": patch(
            "app.agents.orchestrator.calculate_technicals", return_value=technicals
        ),
        "calculate_fundamentals": patch(
            "app.agents.orchestrator.calculate_fundamentals", return_value=fundamentals
        ),
        "fetch_news_headlines": patch(
            "app.agents.orchestrator.fetch_news_headlines", return_value=headlines
        ),
        "analyze_sentiment": patch(
            "app.agents.orchestrator.analyze_sentiment",
            new_callable=AsyncMock,
            return_value=(sentiment, headlines or []),
        ),
        "run_agent": patch(
            "app.agents.orchestrator.run_agent",
            new_callable=AsyncMock,
            return_value=agent_result or AgentResult(),
        ),
    }


# ---------------------------------------------------------------------------
# _compute_weighted_confidence tests
# ---------------------------------------------------------------------------


class TestComputeWeightedConfidence:
    def test_all_three_pillars(self, sample_technicals, sample_fundamentals, sample_sentiment):
        confidence = _compute_weighted_confidence(
            sample_technicals, sample_fundamentals, sample_sentiment
        )
        # 0.40 * 0.70 + 0.40 * 0.60 + 0.20 * 0.55 = 0.28 + 0.24 + 0.11 = 0.63
        assert confidence == 0.63

    def test_no_fundamentals(self, sample_technicals, sample_sentiment):
        confidence = _compute_weighted_confidence(sample_technicals, None, sample_sentiment)
        # 0.70 * 0.70 + 0.30 * 0.55 = 0.49 + 0.165 = 0.655
        assert confidence == 0.655

    def test_no_sentiment(self, sample_technicals, sample_fundamentals):
        confidence = _compute_weighted_confidence(sample_technicals, sample_fundamentals, None)
        # 0.60 * 0.70 + 0.40 * 0.60 = 0.42 + 0.24 = 0.66
        assert confidence == 0.66

    def test_technical_only(self, sample_technicals):
        confidence = _compute_weighted_confidence(sample_technicals, None, None)
        # 1.00 * 0.70 = 0.70
        assert confidence == 0.70

    def test_no_data_returns_neutral(self):
        confidence = _compute_weighted_confidence(None, None, None)
        assert confidence == 0.5

    def test_clamps_to_range(self):
        tech = TechnicalAnalysis(technical_score=1.5)
        confidence = _compute_weighted_confidence(tech, None, None)
        assert confidence <= 1.0


# ---------------------------------------------------------------------------
# Orchestrator integration tests
# ---------------------------------------------------------------------------


class TestOrchestratorHappyPath:
    @pytest.mark.asyncio
    async def test_returns_full_response(
        self, sample_price, sample_technicals, sample_fundamentals,
        sample_headlines, sample_sentiment, sample_agent_result,
    ):
        patches = _patch_all(
            price=sample_price,
            technicals=sample_technicals,
            fundamentals=sample_fundamentals,
            headlines=sample_headlines,
            sentiment=sample_sentiment,
            agent_result=sample_agent_result,
        )

        with patches["get_ticker"], patches["get_stock_price"], \
             patches["get_company_name"], patches["calculate_technicals"], \
             patches["calculate_fundamentals"], patches["fetch_news_headlines"], \
             patches["analyze_sentiment"], patches["run_agent"]:

            orchestrator = StockAnalysisOrchestrator()
            result = await orchestrator.analyze(AnalyzeRequest(ticker="AAPL"))

        assert result.ticker == "AAPL"
        assert result.company_name == "Apple Inc."
        assert result.signal == SignalType.BUY
        assert result.explanation == "Strong outlook."
        assert result.price_data == sample_price
        assert result.analysis.technical == sample_technicals
        assert result.analysis.fundamentals == sample_fundamentals
        assert result.analysis.sentiment == sample_sentiment
        assert len(result.sources) == 2
        assert result.metadata.cached is False


class TestOrchestratorCache:
    @pytest.mark.asyncio
    async def test_second_call_returns_cached(
        self, sample_price, sample_technicals, sample_fundamentals,
        sample_headlines, sample_sentiment, sample_agent_result,
    ):
        patches = _patch_all(
            price=sample_price,
            technicals=sample_technicals,
            fundamentals=sample_fundamentals,
            headlines=sample_headlines,
            sentiment=sample_sentiment,
            agent_result=sample_agent_result,
        )

        with patches["get_ticker"] as mock_ticker, patches["get_stock_price"], \
             patches["get_company_name"], patches["calculate_technicals"], \
             patches["calculate_fundamentals"], patches["fetch_news_headlines"], \
             patches["analyze_sentiment"], patches["run_agent"] as mock_agent:

            orchestrator = StockAnalysisOrchestrator()
            first = await orchestrator.analyze(AnalyzeRequest(ticker="AAPL"))
            second = await orchestrator.analyze(AnalyzeRequest(ticker="AAPL"))

        assert first.metadata.cached is False
        assert second.metadata.cached is True
        # Agent should only be called once (first request)
        mock_agent.assert_called_once()


class TestOrchestratorGracefulDegradation:
    @pytest.mark.asyncio
    async def test_fundamentals_unavailable(
        self, sample_price, sample_technicals, sample_headlines,
        sample_sentiment, sample_agent_result,
    ):
        patches = _patch_all(
            price=sample_price,
            technicals=sample_technicals,
            fundamentals=None,
            headlines=sample_headlines,
            sentiment=sample_sentiment,
            agent_result=sample_agent_result,
        )
        # Make fundamentals raise an error
        patches["calculate_fundamentals"] = patch(
            "app.agents.orchestrator.calculate_fundamentals",
            side_effect=ValueError("No fundamental data"),
        )

        with patches["get_ticker"], patches["get_stock_price"], \
             patches["get_company_name"], patches["calculate_technicals"], \
             patches["calculate_fundamentals"], patches["fetch_news_headlines"], \
             patches["analyze_sentiment"], patches["run_agent"]:

            orchestrator = StockAnalysisOrchestrator()
            result = await orchestrator.analyze(AnalyzeRequest(ticker="VOO"))

        assert result.analysis.fundamentals is None
        assert result.analysis.technical is not None
        assert result.analysis.sentiment is not None

    @pytest.mark.asyncio
    async def test_news_unavailable(
        self, sample_price, sample_technicals, sample_fundamentals,
        sample_agent_result,
    ):
        patches = _patch_all(
            price=sample_price,
            technicals=sample_technicals,
            fundamentals=sample_fundamentals,
            headlines=None,
            sentiment=None,
            agent_result=sample_agent_result,
        )
        # Make news raise an error
        patches["fetch_news_headlines"] = patch(
            "app.agents.orchestrator.fetch_news_headlines",
            side_effect=RuntimeError("API down"),
        )

        with patches["get_ticker"], patches["get_stock_price"], \
             patches["get_company_name"], patches["calculate_technicals"], \
             patches["calculate_fundamentals"], patches["fetch_news_headlines"], \
             patches["analyze_sentiment"] as mock_sentiment, patches["run_agent"]:

            orchestrator = StockAnalysisOrchestrator()
            result = await orchestrator.analyze(AnalyzeRequest(ticker="AAPL"))

        assert result.analysis.sentiment is None
        assert result.sources == []
        # Sentiment should not have been called since no headlines
        mock_sentiment.assert_not_called()

    @pytest.mark.asyncio
    async def test_company_name_none(
        self, sample_price, sample_technicals, sample_agent_result,
    ):
        patches = _patch_all(
            price=sample_price,
            technicals=sample_technicals,
            agent_result=sample_agent_result,
            company_name=None,
        )

        with patches["get_ticker"], patches["get_stock_price"], \
             patches["get_company_name"], patches["calculate_technicals"], \
             patches["calculate_fundamentals"], patches["fetch_news_headlines"], \
             patches["analyze_sentiment"], patches["run_agent"]:

            orchestrator = StockAnalysisOrchestrator()
            result = await orchestrator.analyze(
                AnalyzeRequest(ticker="XYZ", include_fundamentals=False, include_news=False)
            )

        assert result.company_name is None


class TestOrchestratorOptionalPillars:
    @pytest.mark.asyncio
    async def test_include_fundamentals_false_skips_call(
        self, sample_price, sample_technicals, sample_agent_result,
    ):
        patches = _patch_all(
            price=sample_price,
            technicals=sample_technicals,
            agent_result=sample_agent_result,
        )

        with patches["get_ticker"], patches["get_stock_price"], \
             patches["get_company_name"], patches["calculate_technicals"], \
             patches["calculate_fundamentals"] as mock_fund, \
             patches["fetch_news_headlines"], patches["analyze_sentiment"], \
             patches["run_agent"]:

            orchestrator = StockAnalysisOrchestrator()
            result = await orchestrator.analyze(
                AnalyzeRequest(ticker="AAPL", include_fundamentals=False)
            )

        mock_fund.assert_not_called()
        assert result.analysis.fundamentals is None

    @pytest.mark.asyncio
    async def test_include_news_false_skips_news_and_sentiment(
        self, sample_price, sample_technicals, sample_agent_result,
    ):
        patches = _patch_all(
            price=sample_price,
            technicals=sample_technicals,
            agent_result=sample_agent_result,
        )

        with patches["get_ticker"], patches["get_stock_price"], \
             patches["get_company_name"], patches["calculate_technicals"], \
             patches["calculate_fundamentals"], \
             patches["fetch_news_headlines"] as mock_news, \
             patches["analyze_sentiment"] as mock_sent, patches["run_agent"]:

            orchestrator = StockAnalysisOrchestrator()
            result = await orchestrator.analyze(
                AnalyzeRequest(ticker="AAPL", include_news=False)
            )

        mock_news.assert_not_called()
        mock_sent.assert_not_called()
        assert result.analysis.sentiment is None
        assert result.sources == []

    @pytest.mark.asyncio
    async def test_include_technicals_false_skips_call(
        self, sample_price, sample_agent_result,
    ):
        patches = _patch_all(
            price=sample_price,
            agent_result=sample_agent_result,
        )

        with patches["get_ticker"], patches["get_stock_price"], \
             patches["get_company_name"], \
             patches["calculate_technicals"] as mock_tech, \
             patches["calculate_fundamentals"], patches["fetch_news_headlines"], \
             patches["analyze_sentiment"], patches["run_agent"]:

            orchestrator = StockAnalysisOrchestrator()
            result = await orchestrator.analyze(
                AnalyzeRequest(ticker="AAPL", include_technicals=False)
            )

        mock_tech.assert_not_called()
        assert result.analysis.technical is None


class TestOrchestratorErrorCases:
    @pytest.mark.asyncio
    async def test_invalid_ticker_raises_value_error(self):
        """When price_data is None (invalid ticker), orchestrator raises ValueError."""
        patches = _patch_all(price=None)

        with patches["get_ticker"], patches["get_stock_price"], \
             patches["get_company_name"], patches["calculate_technicals"], \
             patches["calculate_fundamentals"], patches["fetch_news_headlines"], \
             patches["analyze_sentiment"], patches["run_agent"]:

            orchestrator = StockAnalysisOrchestrator()
            with pytest.raises(ValueError, match="not found"):
                await orchestrator.analyze(AnalyzeRequest(ticker="INVALID"))

    @pytest.mark.asyncio
    async def test_agent_exception_uses_hold_fallback(self, sample_price):
        """When run_agent raises a generic exception, orchestrator returns HOLD fallback."""
        patches = _patch_all(price=sample_price)
        patches["run_agent"] = patch(
            "app.agents.orchestrator.run_agent",
            new_callable=AsyncMock,
            side_effect=RuntimeError("Agent crashed"),
        )

        with patches["get_ticker"], patches["get_stock_price"], \
             patches["get_company_name"], patches["calculate_technicals"], \
             patches["calculate_fundamentals"], patches["fetch_news_headlines"], \
             patches["analyze_sentiment"], patches["run_agent"]:

            orchestrator = StockAnalysisOrchestrator()
            result = await orchestrator.analyze(
                AnalyzeRequest(
                    ticker="AAPL",
                    include_technicals=False,
                    include_fundamentals=False,
                    include_news=False,
                )
            )

        assert result.signal == SignalType.HOLD
        assert "unavailable" in result.explanation.lower()


class TestOrchestratorAgentFallback:
    @pytest.mark.asyncio
    async def test_agent_invalid_json_defaults_to_hold(self, sample_price):
        patches = _patch_all(
            price=sample_price,
            agent_result=AgentResult(),  # defaults: HOLD, 0.5, ""
        )

        with patches["get_ticker"], patches["get_stock_price"], \
             patches["get_company_name"], patches["calculate_technicals"], \
             patches["calculate_fundamentals"], patches["fetch_news_headlines"], \
             patches["analyze_sentiment"], patches["run_agent"]:

            orchestrator = StockAnalysisOrchestrator()
            result = await orchestrator.analyze(
                AnalyzeRequest(ticker="AAPL", include_technicals=False,
                               include_fundamentals=False, include_news=False)
            )

        assert result.signal == SignalType.HOLD
