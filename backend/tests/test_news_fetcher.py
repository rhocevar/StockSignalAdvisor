from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.agents.tools.news_fetcher import (
    _NEWSAPI_FIELD_MAP,
    _build_news_query,
    _is_english_headline,
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


# ---- _build_news_query Tests ----

class TestBuildNewsQuery:
    def test_no_company_name_returns_ticker(self):
        assert _build_news_query("AAPL", None) == "AAPL"

    def test_with_company_name_returns_brand_name(self):
        # When a brand name is available, use it alone — the ticker is NOT included.
        # This prevents ticker-as-noise contamination (e.g. PBR → Unity/3D-graphics articles).
        assert _build_news_query("AAPL", "Apple Inc.") == '"Apple"'

    def test_strips_legal_suffixes(self):
        assert _build_news_query("MSFT", "Microsoft Corporation") == '"Microsoft"'
        assert _build_news_query("NVDA", "NVIDIA Corporation") == '"NVIDIA"'
        assert _build_news_query("TSLA", "Tesla, Inc.") == '"Tesla"'

    def test_extracts_brand_name_after_dash(self):
        # The canonical PBR bug: bare "PBR" matches Unity game-dev articles.
        # Using just "Petrobras" eliminates all non-finance noise.
        result = _build_news_query("PBR", "Petróleo Brasileiro S.A. - Petrobras")
        assert result == '"Petrobras"'

    def test_company_name_same_as_ticker_returns_ticker(self):
        # When brand name equals the ticker, fall back to plain ticker (no quotes needed).
        assert _build_news_query("XYZ", "XYZ") == "XYZ"

    def test_empty_company_name_returns_ticker(self):
        assert _build_news_query("AAPL", "") == "AAPL"

    def test_strips_company_suffix(self):
        assert _build_news_query("MMM", "3M Company") == '"3M"'

    def test_strips_leading_the_and_company(self):
        # "The Walt Disney Company" → strip "The " → strip "Company" → "Walt Disney"
        assert _build_news_query("DIS", "The Walt Disney Company") == '"Walt Disney"'

    def test_strips_leading_the_with_inc(self):
        assert _build_news_query("HD", "The Home Depot, Inc.") == '"Home Depot"'

    def test_strips_european_ag_long_form(self):
        # Bayer's yfinance longName uses the full German legal form
        assert _build_news_query("BAYRY", "Bayer Aktiengesellschaft") == '"Bayer"'

    def test_strips_european_se_suffix(self):
        assert _build_news_query("BNTX", "BioNTech SE") == '"BioNTech"'

    def test_european_se_same_as_ticker_returns_ticker(self):
        # "SAP SE" → strip SE → "SAP" == ticker → fall back to plain ticker
        assert _build_news_query("SAP", "SAP SE") == "SAP"

    def test_strips_nordic_as_suffix(self):
        assert _build_news_query("NVO", "Novo Nordisk A/S") == '"Novo Nordisk"'

    def test_strips_parenthetical_adr(self):
        assert _build_news_query("HDB", "HDFC Bank Limited (ADR)") == '"HDFC Bank"'

    def test_strips_holdings_suffix(self):
        assert _build_news_query("PYPL", "PayPal Holdings, Inc.") == '"PayPal"'


# ---- _is_english_headline Tests ----

class TestIsEnglishHeadline:
    def test_plain_english_passes(self):
        assert _is_english_headline("Apple Reports Record Revenue in Q4") is True

    def test_empty_string_fails(self):
        assert _is_english_headline("") is False

    def test_japanese_title_fails(self):
        # Headline from Applech2.com seen in production
        assert _is_english_headline(
            "Belkin、Qi2 25Wワイヤレス充電器とApple Watch充電器を備えコンパクトに収納可能な"
        ) is False

    def test_mostly_english_with_minor_accents_passes(self):
        # Accented characters in proper nouns should not disqualify an article
        assert _is_english_headline("Café chain Starbucks beats AAPL in customer retention") is True

    def test_fully_ascii_passes(self):
        assert _is_english_headline("AAPL hits new 52-week high") is True


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
    def test_skips_non_english_titles(self, mock_get, mock_settings):
        mock_settings.NEWS_API_KEY = "test-key"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "ok",
            "articles": [
                {
                    "source": {"name": "Applech2"},
                    "title": "Belkin、Qi2 25Wワイヤレス充電器とApple Watch充電器を備えコンパクト",
                    "url": "http://applech2.com/1",
                },
                {
                    "source": {"name": "Reuters"},
                    "title": "Apple reports quarterly earnings",
                    "url": "http://reuters.com/1",
                },
            ],
        }
        mock_get.return_value = mock_response

        result = fetch_news_headlines("AAPL")

        assert len(result) == 1
        assert result[0].title == "Apple reports quarterly earnings"

    @patch("app.agents.tools.news_fetcher.settings")
    @patch("app.agents.tools.news_fetcher.requests.get")
    def test_searches_title_only(self, mock_get, mock_settings, mock_newsapi_response):
        # Title-only ensures we fetch articles *about* the company, not ones that
        # mention it in passing (sponsor lists, footnotes, package descriptions).
        mock_settings.NEWS_API_KEY = "test-key"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_newsapi_response
        mock_get.return_value = mock_response

        fetch_news_headlines("AAPL")

        call_params = mock_get.call_args[1]["params"]
        assert call_params["searchIn"] == "title"

    @patch("app.agents.tools.news_fetcher.settings")
    @patch("app.agents.tools.news_fetcher.requests.get")
    def test_excludes_pypi_domain(self, mock_get, mock_settings, mock_newsapi_response):
        mock_settings.NEWS_API_KEY = "test-key"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_newsapi_response
        mock_get.return_value = mock_response

        fetch_news_headlines("AAPL")

        call_params = mock_get.call_args[1]["params"]
        assert "pypi.org" in call_params["excludeDomains"]

    @patch("app.agents.tools.news_fetcher.settings")
    @patch("app.agents.tools.news_fetcher.requests.get")
    def test_uses_company_name_in_query_when_provided(self, mock_get, mock_settings, mock_newsapi_response):
        mock_settings.NEWS_API_KEY = "test-key"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_newsapi_response
        mock_get.return_value = mock_response

        fetch_news_headlines("PBR", "Petróleo Brasileiro S.A. - Petrobras")

        call_params = mock_get.call_args[1]["params"]
        assert call_params["q"] == '"Petrobras"'

    @patch("app.agents.tools.news_fetcher.settings")
    @patch("app.agents.tools.news_fetcher.requests.get")
    def test_uses_ticker_only_when_no_company_name(self, mock_get, mock_settings, mock_newsapi_response):
        mock_settings.NEWS_API_KEY = "test-key"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_newsapi_response
        mock_get.return_value = mock_response

        fetch_news_headlines("AAPL")

        call_params = mock_get.call_args[1]["params"]
        assert call_params["q"] == "AAPL"

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
