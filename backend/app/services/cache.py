"""Simple TTL cache for analysis results, keyed by uppercased ticker."""

from cachetools import TTLCache

from app.config import settings
from app.models.response import AnalyzeResponse

_cache: TTLCache = TTLCache(maxsize=128, ttl=settings.CACHE_TTL_SECONDS)


def get_cached(ticker: str) -> AnalyzeResponse | None:
    return _cache.get(ticker.upper())


def set_cached(ticker: str, result: AnalyzeResponse) -> None:
    _cache[ticker.upper()] = result


def clear_cache() -> None:
    _cache.clear()
