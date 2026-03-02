import re
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

# Headlines where more than this fraction of characters are non-ASCII are treated
# as non-English and discarded. NewsAPI's language filter is unreliable for sources
# that publish in multiple languages (e.g. Japanese tech blogs).
_NON_ASCII_THRESHOLD = 0.15

# Legal entity suffixes to strip when building a human-readable company name
# for use in a NewsAPI query (e.g. "Apple Inc." → "Apple").
# Covers the most common US, European, and international formats returned by yfinance.
_LEGAL_SUFFIX_RE = re.compile(
    r"\s*\b("
    # English / general
    r"Inc\.?|Corp\.?|Ltd\.?|LLC|Company|Limited|Corporation|Incorporated|"
    # Ampersand constructs
    r"& Co\.?|"
    # British
    r"PLC|"
    # European continental
    r"AG|SE|GmbH|Aktiengesellschaft|"
    # Dutch / Italian (already present, kept for clarity)
    r"N\.V\.|S\.p\.A\.|"
    # Spanish / Portuguese
    r"S\.A\.?|"
    # Nordic
    r"A/S|"
    # Trailing structural qualifier often left after other suffix stripping
    r"Holdings?"
    r")\b",
    re.IGNORECASE,
)


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


def _is_english_headline(title: str) -> bool:
    """Return True if the headline is likely written in English.

    Rejects titles where more than 15% of characters are non-ASCII, which
    catches Japanese, Korean, and Chinese headlines that slip through
    NewsAPI's language filter on mixed-language publisher domains.
    """
    if not title:
        return False
    non_ascii = sum(1 for c in title if ord(c) > 127)
    return non_ascii / len(title) <= _NON_ASCII_THRESHOLD


def _build_news_query(ticker: str, company_name: str | None) -> str:
    """Build a NewsAPI q-string that targets the company's brand name.

    Strategy: when a recognisable brand name can be extracted from the company name,
    search by that brand name alone.  Using the ticker as an OR fallback is
    insufficient — short tickers are often common abbreviations in unrelated fields
    (e.g. "PBR" matches hundreds of daily Unity Asset Store articles about Physically
    Based Rendering), so mixing it into the query contaminates results even when the
    brand-name term is also present.

    Normalization steps applied to the company name:
      1. Extract brand name after " - " separator (e.g. "Petróleo Brasileiro S.A. - Petrobras")
      2. Strip parenthetical qualifiers (e.g. "(ADR)", "(ADS)")
      3. Strip leading "The " article
      4. Strip legal/entity suffixes (Inc., Corp., AG, SE, A/S, Aktiengesellschaft, etc.)
      5. Strip trailing punctuation

    Examples:
      ("PBR",  "Petróleo Brasileiro S.A. - Petrobras") → '"Petrobras"'
      ("AAPL", "Apple Inc.")                           → '"Apple"'
      ("DIS",  "The Walt Disney Company")              → '"Walt Disney"'
      ("NVO",  "Novo Nordisk A/S")                     → '"Novo Nordisk"'
      ("SAP",  "SAP SE")                               → 'SAP'   (brand == ticker → plain ticker)
      ("HDB",  "HDFC Bank Limited (ADR)")              → '"HDFC Bank"'
      ("TSLA", None)                                   → 'TSLA'  (no company name → plain ticker)
    """
    if not company_name:
        return ticker

    name = company_name

    # If the full legal name contains " - ", the brand name follows it.
    # e.g. "Petróleo Brasileiro S.A. - Petrobras" → "Petrobras"
    if " - " in name:
        name = name.split(" - ")[-1].strip()

    # Strip parenthetical qualifiers appended by yfinance (e.g. "(ADR)", "(ADS)").
    name = re.sub(r"\s*\([^)]+\)", "", name).strip()

    # Strip leading English article that yfinance includes for some companies
    # (e.g. "The Walt Disney Company" → "Walt Disney Company").
    name = re.sub(r"^The\s+", "", name, flags=re.IGNORECASE).strip()

    # Strip common legal entity suffixes.
    name = _LEGAL_SUFFIX_RE.sub("", name)

    # Strip trailing punctuation and whitespace left after suffix removal.
    name = re.sub(r"[,.\s]+$", "", name).strip()

    # If nothing useful remains or the name equals the ticker, skip the brand query.
    if not name or name.upper() == ticker.upper():
        return ticker

    # Use the brand name alone — do NOT include the ticker as an OR alternative.
    # Adding the ticker contaminates results when the ticker is also a common
    # abbreviation in an unrelated field (e.g. PBR → Physically Based Rendering).
    return f'"{name}"'


def fetch_news_headlines(ticker: str, company_name: str | None = None, max_results: int = 10) -> list[NewsSource]:
    """Fetch recent news headlines for a ticker from NewsAPI."""
    if not settings.NEWS_API_KEY:
        raise ValueError("NEWS_API_KEY is not configured")

    # Request extra articles to have headroom after the language filter removes
    # non-English results. Capped at NewsAPI's maximum page size of 100.
    fetch_size = min(max_results * 2, 100)

    response = requests.get(
        _NEWSAPI_BASE_URL,
        params={
            "q": _build_news_query(ticker, company_name),
            "sortBy": "publishedAt",
            "pageSize": fetch_size,
            "language": "en",
            # Restrict to title only — articles that mention the company only in
            # passing (sponsors lists, description footnotes) are irrelevant to
            # financial sentiment and should not be fetched.  Articles that are
            # *about* the company always name it in the headline.
            "searchIn": "title",
            # Exclude package-registry feeds: PyPI publishes a news entry per
            # release, and packages with a company's name in their identifier
            # (e.g. "sap-hana-ml 2.22.0") would otherwise flood results.
            "excludeDomains": "pypi.org",
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
        if len(results) >= max_results:
            break

        data: dict = {}
        for api_key, field_name in _NEWSAPI_FIELD_MAP:
            data[field_name] = _get_nested(article, api_key)

        if data.get("published_at"):
            data["published_at"] = _parse_published_at(data["published_at"])

        title = data.get("title")
        if title and _is_english_headline(title):
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
