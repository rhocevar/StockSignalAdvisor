from datetime import datetime
from typing import Any

import requests

from app.config import settings
from app.models.domain import NewsSource

_NEWSAPI_BASE_URL = "https://newsapi.org/v2/everything"

# Centralized mapping: (newsapi_article_key, NewsSource_field_name)
# Nested keys use dot notation (e.g. "source.name") and are resolved by _get_nested.
_NEWSAPI_FIELD_MAP: list[tuple[str, str]] = [
    ("title", "title"),
    ("source.name", "source"),
    ("url", "url"),
    ("publishedAt", "published_at"),
]


def _get_nested(data: dict, dot_path: str) -> Any:
    """Resolve a dot-notation path in a nested dict (e.g. 'source.name')."""
    keys = dot_path.split(".")
    value = data
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def _parse_published_at(value: Any) -> datetime | None:
    """Parse an ISO 8601 datetime string from NewsAPI."""
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def fetch_news_headlines(ticker: str, max_results: int = 10) -> list[NewsSource]:
    """Fetch recent news headlines for a ticker from NewsAPI."""
    if not settings.NEWS_API_KEY:
        raise ValueError("NEWS_API_KEY is not configured")

    response = requests.get(
        _NEWSAPI_BASE_URL,
        params={
            "q": ticker,
            "sortBy": "publishedAt",
            "pageSize": max_results,
            "language": "en",
            "apiKey": settings.NEWS_API_KEY,
        },
        timeout=10,
    )

    if response.status_code != 200:
        raise ValueError(
            f"NewsAPI request failed with status {response.status_code}: "
            f"{response.json().get('message', 'Unknown error')}"
        )

    articles = response.json().get("articles", [])
    results: list[NewsSource] = []

    for article in articles:
        data: dict = {}
        for api_key, field_name in _NEWSAPI_FIELD_MAP:
            data[field_name] = _get_nested(article, api_key)

        if data.get("published_at"):
            data["published_at"] = _parse_published_at(data["published_at"])

        if data.get("title"):
            results.append(NewsSource(**data))

    return results


def format_headlines(articles: list[NewsSource]) -> str:
    """Format a list of NewsSource articles into a numbered text block."""
    if not articles:
        return "No recent news found."

    lines: list[str] = []
    for i, article in enumerate(articles, 1):
        source_tag = f"[{article.source}] " if article.source else ""
        date_tag = ""
        if article.published_at:
            date_tag = f" ({article.published_at.strftime('%Y-%m-%d')})"
        lines.append(f"{i}. {source_tag}{article.title}{date_tag}")

    return "\n".join(lines)


def get_news_headlines(ticker: str) -> str:
    """Fetch and format news headlines for a ticker (LangChain tool interface)."""
    articles = fetch_news_headlines(ticker)
    return format_headlines(articles)
