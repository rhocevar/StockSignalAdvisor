from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.agents.tools.news_fetcher import (
    _NEWSAPI_FIELD_MAP,
    fetch_news_headlines,
    format_headlines,
    get_news_headlines,
)
from app.models.domain import NewsSource


@pytest.fixture
def mock_newsapi_response():
    """A successful NewsAPI response with 2 articles."""
    return {
        "status": "ok",
        "totalResults": 2,
        "articles": [
            {
                "source": {"id": "reuters", "name": "Reuters"},
                "title": "Apple iPhone Sales Drop in China",
                "url": "https://reuters.com/article/1",
                "publishedAt": "2025-02-14T10:30:00Z",
                "description": "Sales dropped 5%...",
            },
            {
                "source": {"id": "bloomberg", "name": "Bloomberg"},
                "title": "Apple Reports Record Services Revenue",
                "url": "https://bloomberg.com/article/2",
                "publishedAt": "2025-02-14T08:00:00Z",
                "description": "Services revenue hit $25B...",
            },
        ],
    }


@pytest.fixture
def sample_articles():
    """Pre-built NewsSource list for format tests."""
    return [
        NewsSource(
            title="Apple iPhone Sales Drop in China",
            source="Reuters",
            url="https://reuters.com/article/1",
            published_at=datetime(2025, 2, 14, 10, 30, tzinfo=timezone.utc),
        ),
        NewsSource(
            title="Apple Reports Record Services Revenue",
            source="Bloomberg",
            url="https://bloomberg.com/article/2",
            published_at=datetime(2025, 2, 14, 8, 0, tzinfo=timezone.utc),
        ),
    ]


# ---- Field Mapping Tests ----

class TestFieldMapping:
    def test_all_mapping_fields_exist_on_model(self):
        model_fields = set(NewsSource.model_fields.keys())
        for _, field_name in _NEWSAPI_FIELD_MAP:
            assert field_name in model_fields, f"Mapping references unknown field: {field_name}"

    def test_mapping_has_no_duplicate_model_fields(self):
        field_names = [field_name for _, field_name in _NEWSAPI_FIELD_MAP]
        assert len(field_names) == len(set(field_names))


# ---- fetch_news_headlines Tests ----

class TestFetchNewsHeadlines:
    @patch("app.agents.tools.news_fetcher.settings")
    @patch("app.agents.tools.news_fetcher.requests.get")
    def test_returns_news_sources(self, mock_get, mock_settings, mock_newsapi_response):
        mock_settings.NEWS_API_KEY = "test-key"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_newsapi_response
        mock_get.return_value = mock_response

        result = fetch_news_headlines("AAPL")

        assert len(result) == 2
        assert all(isinstance(a, NewsSource) for a in result)

    @patch("app.agents.tools.news_fetcher.settings")
    @patch("app.agents.tools.news_fetcher.requests.get")
    def test_maps_fields_correctly(self, mock_get, mock_settings, mock_newsapi_response):
        mock_settings.NEWS_API_KEY = "test-key"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_newsapi_response
        mock_get.return_value = mock_response

        result = fetch_news_headlines("AAPL")

        assert result[0].title == "Apple iPhone Sales Drop in China"
        assert result[0].source == "Reuters"
        assert result[0].url == "https://reuters.com/article/1"
        assert result[0].sentiment is None  # Not set until LLM analysis

    @patch("app.agents.tools.news_fetcher.settings")
    @patch("app.agents.tools.news_fetcher.requests.get")
    def test_parses_published_at(self, mock_get, mock_settings, mock_newsapi_response):
        mock_settings.NEWS_API_KEY = "test-key"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_newsapi_response
        mock_get.return_value = mock_response

        result = fetch_news_headlines("AAPL")

        assert result[0].published_at is not None
        assert isinstance(result[0].published_at, datetime)
        assert result[0].published_at.year == 2025
        assert result[0].published_at.month == 2
        assert result[0].published_at.day == 14

    @patch("app.agents.tools.news_fetcher.settings")
    @patch("app.agents.tools.news_fetcher.requests.get")
    def test_empty_articles(self, mock_get, mock_settings):
        mock_settings.NEWS_API_KEY = "test-key"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok", "totalResults": 0, "articles": []}
        mock_get.return_value = mock_response

        result = fetch_news_headlines("AAPL")

        assert result == []

    @patch("app.agents.tools.news_fetcher.settings")
    @patch("app.agents.tools.news_fetcher.requests.get")
    def test_api_error_raises(self, mock_get, mock_settings):
        mock_settings.NEWS_API_KEY = "test-key"
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"status": "error", "message": "Invalid API key"}
        mock_get.return_value = mock_response

        with pytest.raises(ValueError, match="NewsAPI request failed"):
            fetch_news_headlines("AAPL")

    @patch("app.agents.tools.news_fetcher.settings")
    def test_missing_api_key_raises(self, mock_settings):
        mock_settings.NEWS_API_KEY = None

        with pytest.raises(ValueError, match="NEWS_API_KEY is not configured"):
            fetch_news_headlines("AAPL")

    @patch("app.agents.tools.news_fetcher.settings")
    @patch("app.agents.tools.news_fetcher.requests.get")
    def test_skips_articles_without_title(self, mock_get, mock_settings):
        mock_settings.NEWS_API_KEY = "test-key"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "ok",
            "articles": [
                {"source": {"name": "Test"}, "title": None, "url": "http://x.com"},
                {"source": {"name": "Reuters"}, "title": "Valid Article", "url": "http://y.com"},
            ],
        }
        mock_get.return_value = mock_response

        result = fetch_news_headlines("AAPL")

        assert len(result) == 1
        assert result[0].title == "Valid Article"


# ---- format_headlines Tests ----

class TestFormatHeadlines:
    def test_formats_numbered_list(self, sample_articles):
        result = format_headlines(sample_articles)

        assert "1. [Reuters] Apple iPhone Sales Drop in China (2025-02-14)" in result
        assert "2. [Bloomberg] Apple Reports Record Services Revenue (2025-02-14)" in result

    def test_empty_list(self):
        result = format_headlines([])

        assert result == "No recent news found."

    def test_article_without_source(self):
        articles = [NewsSource(title="Test Article")]
        result = format_headlines(articles)

        assert "1. Test Article" in result
        assert "[" not in result

    def test_article_without_date(self):
        articles = [NewsSource(title="Test Article", source="Reuters")]
        result = format_headlines(articles)

        assert "1. [Reuters] Test Article" in result
        assert "(" not in result


# ---- get_news_headlines End-to-End Test ----

class TestGetNewsHeadlines:
    @patch("app.agents.tools.news_fetcher.settings")
    @patch("app.agents.tools.news_fetcher.requests.get")
    def test_returns_formatted_string(self, mock_get, mock_settings, mock_newsapi_response):
        mock_settings.NEWS_API_KEY = "test-key"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_newsapi_response
        mock_get.return_value = mock_response

        result = get_news_headlines("AAPL")

        assert isinstance(result, str)
        assert "Apple iPhone Sales Drop in China" in result
        assert "Apple Reports Record Services Revenue" in result
        assert "1." in result
        assert "2." in result
