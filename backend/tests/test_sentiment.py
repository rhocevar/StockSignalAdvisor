"""Tests for LLM-powered sentiment analysis."""

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.enums import SentimentType
from app.models.domain import NewsSource, SentimentAnalysis
from app.providers.llm.base import LLMResponse


def _make_headlines(count: int = 3) -> list[NewsSource]:
    """Create sample NewsSource objects for testing."""
    titles = [
        "Apple Reports Record Revenue for Q4",
        "iPhone Sales Decline in China Market",
        "Apple Announces New Product Launch Date",
    ]
    return [
        NewsSource(
            title=titles[i % len(titles)],
            source=f"Source{i}",
            url=f"https://example.com/{i}",
            published_at=datetime(2025, 2, 14, tzinfo=timezone.utc),
        )
        for i in range(count)
    ]


def _mock_llm_response(data: dict) -> LLMResponse:
    """Create a mock LLMResponse with JSON content."""
    return LLMResponse(
        content=json.dumps(data),
        model="gpt-4o-mini",
        usage={"prompt_tokens": 100, "completion_tokens": 50},
    )


def _make_provider(response_data: dict) -> MagicMock:
    """Create a mock LLM provider returning the given JSON data."""
    provider = MagicMock()
    provider.complete = AsyncMock(return_value=_mock_llm_response(response_data))
    return provider


_HAPPY_RESPONSE = {
    "headlines": [
        {"index": 0, "sentiment": "positive"},
        {"index": 1, "sentiment": "negative"},
        {"index": 2, "sentiment": "neutral"},
    ],
    "overall": "mixed",
    "score": 0.55,
}


class TestAnalyzeSentiment:
    @pytest.mark.asyncio
    @patch("app.agents.tools.sentiment.get_llm_provider")
    async def test_happy_path(self, mock_factory):
        mock_factory.return_value = _make_provider(_HAPPY_RESPONSE)

        from app.agents.tools.sentiment import analyze_sentiment

        headlines = _make_headlines(3)
        result, _ = await analyze_sentiment(headlines)

        assert isinstance(result, SentimentAnalysis)
        assert result.overall == SentimentType.MIXED
        assert result.score == 0.55
        assert result.positive_count == 1
        assert result.negative_count == 1
        assert result.neutral_count == 1

    @pytest.mark.asyncio
    async def test_empty_headlines_returns_neutral(self):
        from app.agents.tools.sentiment import analyze_sentiment

        result, updated = await analyze_sentiment([])

        assert result.overall == SentimentType.NEUTRAL
        assert result.score == 0.5
        assert result.positive_count == 0
        assert result.negative_count == 0
        assert result.neutral_count == 0
        assert updated == []

    @pytest.mark.asyncio
    @patch("app.agents.tools.sentiment.get_llm_provider")
    async def test_empty_headlines_does_not_call_llm(self, mock_factory):
        from app.agents.tools.sentiment import analyze_sentiment

        await analyze_sentiment([])
        mock_factory.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.agents.tools.sentiment.get_llm_provider")
    async def test_returns_updated_headlines(self, mock_factory):
        mock_factory.return_value = _make_provider(_HAPPY_RESPONSE)

        from app.agents.tools.sentiment import analyze_sentiment

        headlines = _make_headlines(3)
        _, updated = await analyze_sentiment(headlines)

        # Original list must not be mutated
        assert all(h.sentiment is None for h in headlines)
        # Returned list has per-headline sentiments populated
        assert updated[0].sentiment == SentimentType.POSITIVE
        assert updated[1].sentiment == SentimentType.NEGATIVE
        assert updated[2].sentiment == SentimentType.NEUTRAL

    @pytest.mark.asyncio
    @patch("app.agents.tools.sentiment.get_llm_provider")
    async def test_invalid_json_returns_neutral_fallback(self, mock_factory):
        provider = MagicMock()
        provider.complete = AsyncMock(
            return_value=LLMResponse(
                content="This is not JSON at all",
                model="gpt-4o-mini",
                usage={"prompt_tokens": 10, "completion_tokens": 5},
            )
        )
        mock_factory.return_value = provider

        from app.agents.tools.sentiment import analyze_sentiment

        result, _ = await analyze_sentiment(_make_headlines(2))

        assert result.overall == SentimentType.NEUTRAL
        assert result.score == 0.5

    @pytest.mark.asyncio
    @patch("app.agents.tools.sentiment.get_llm_provider")
    async def test_invalid_score_defaults_to_half(self, mock_factory):
        data = {
            "headlines": [{"index": 0, "sentiment": "positive"}],
            "overall": "positive",
            "score": 1.5,  # Out of range
        }
        mock_factory.return_value = _make_provider(data)

        from app.agents.tools.sentiment import analyze_sentiment

        result, _ = await analyze_sentiment(_make_headlines(1))
        assert result.score == 0.5

    @pytest.mark.asyncio
    @patch("app.agents.tools.sentiment.get_llm_provider")
    async def test_negative_score_defaults_to_half(self, mock_factory):
        data = {
            "headlines": [{"index": 0, "sentiment": "negative"}],
            "overall": "negative",
            "score": -0.3,
        }
        mock_factory.return_value = _make_provider(data)

        from app.agents.tools.sentiment import analyze_sentiment

        result, _ = await analyze_sentiment(_make_headlines(1))
        assert result.score == 0.5

    @pytest.mark.asyncio
    @patch("app.agents.tools.sentiment.get_llm_provider")
    async def test_all_positive_headlines(self, mock_factory):
        data = {
            "headlines": [
                {"index": 0, "sentiment": "positive"},
                {"index": 1, "sentiment": "positive"},
            ],
            "overall": "positive",
            "score": 0.85,
        }
        mock_factory.return_value = _make_provider(data)

        from app.agents.tools.sentiment import analyze_sentiment

        result, _ = await analyze_sentiment(_make_headlines(2))

        assert result.overall == SentimentType.POSITIVE
        assert result.score == 0.85
        assert result.positive_count == 2
        assert result.negative_count == 0

    @pytest.mark.asyncio
    @patch("app.agents.tools.sentiment.get_llm_provider")
    async def test_out_of_range_index_ignored(self, mock_factory):
        data = {
            "headlines": [
                {"index": 0, "sentiment": "positive"},
                {"index": 99, "sentiment": "negative"},  # Out of range
            ],
            "overall": "mixed",
            "score": 0.5,
        }
        mock_factory.return_value = _make_provider(data)

        from app.agents.tools.sentiment import analyze_sentiment

        headlines = _make_headlines(1)
        result, updated = await analyze_sentiment(headlines)

        assert updated[0].sentiment == SentimentType.POSITIVE
        assert result.positive_count == 1
        assert result.negative_count == 1

    @pytest.mark.asyncio
    @patch("app.agents.tools.sentiment.get_llm_provider")
    async def test_unknown_sentiment_treated_as_neutral(self, mock_factory):
        data = {
            "headlines": [{"index": 0, "sentiment": "ambiguous"}],
            "overall": "neutral",
            "score": 0.5,
        }
        mock_factory.return_value = _make_provider(data)

        from app.agents.tools.sentiment import analyze_sentiment

        headlines = _make_headlines(1)
        result, updated = await analyze_sentiment(headlines)

        assert updated[0].sentiment == SentimentType.NEUTRAL
        assert result.neutral_count == 1


class TestPrompts:
    def test_analysis_prompt_exists(self):
        from app.agents.prompts import ANALYSIS_SYSTEM_PROMPT

        assert "Technical Analysis" in ANALYSIS_SYSTEM_PROMPT
        assert "Fundamental Analysis" in ANALYSIS_SYSTEM_PROMPT
        assert "Sentiment Analysis" in ANALYSIS_SYSTEM_PROMPT
        assert "BUY" in ANALYSIS_SYSTEM_PROMPT
        assert "HOLD" in ANALYSIS_SYSTEM_PROMPT
        assert "SELL" in ANALYSIS_SYSTEM_PROMPT

    def test_sentiment_prompt_exists(self):
        from app.agents.prompts import SENTIMENT_SYSTEM_PROMPT

        assert "sentiment" in SENTIMENT_SYSTEM_PROMPT.lower()
        assert "positive" in SENTIMENT_SYSTEM_PROMPT.lower()
        assert "negative" in SENTIMENT_SYSTEM_PROMPT.lower()
        assert "JSON" in SENTIMENT_SYSTEM_PROMPT
