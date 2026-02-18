"""Tests for the TTL cache service."""

from unittest.mock import MagicMock, patch

from app.services.cache import clear_cache, get_cached, set_cached


class TestCache:
    def setup_method(self):
        clear_cache()

    def test_get_cached_returns_none_for_missing(self):
        assert get_cached("AAPL") is None

    def test_set_and_get_round_trip(self):
        response = MagicMock()
        set_cached("AAPL", response)
        assert get_cached("AAPL") is response

    def test_key_is_uppercased(self):
        response = MagicMock()
        set_cached("aapl", response)
        assert get_cached("AAPL") is response
        assert get_cached("aapl") is response

    def test_clear_cache_empties(self):
        set_cached("AAPL", MagicMock())
        set_cached("MSFT", MagicMock())
        clear_cache()
        assert get_cached("AAPL") is None
        assert get_cached("MSFT") is None
