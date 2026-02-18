from unittest.mock import MagicMock

import pandas as pd
import pytest

from app.agents.tools.stock_data import (
    get_company_name,
    get_price_history,
    get_stock_price,
    get_ticker,
)
from app.models.domain import PriceData


@pytest.fixture
def mock_stock_info():
    return {
        "regularMarketPrice": 150.0,
        "currency": "USD",
        "fiftyTwoWeekHigh": 180.0,
        "fiftyTwoWeekLow": 120.0,
        "longName": "Apple Inc.",
        "shortName": "AAPL",
    }


@pytest.fixture
def mock_price_history():
    dates = pd.date_range(end="2024-01-30", periods=30, freq="B")
    return pd.DataFrame(
        {
            "Open": [140 + i * 0.5 for i in range(30)],
            "High": [142 + i * 0.5 for i in range(30)],
            "Low": [138 + i * 0.5 for i in range(30)],
            "Close": [141 + i * 0.5 for i in range(30)],
            "Volume": [1000000 + i * 10000 for i in range(30)],
        },
        index=dates,
    )


@pytest.fixture
def mock_ticker(mock_stock_info, mock_price_history):
    """Create a mock yf.Ticker with info and history pre-configured."""
    ticker = MagicMock()
    ticker.ticker = "AAPL"
    ticker.info = mock_stock_info
    ticker.history.return_value = mock_price_history
    return ticker


class TestGetTicker:
    def test_returns_yf_ticker(self):
        result = get_ticker("AAPL")
        assert result.ticker == "AAPL"


class TestGetStockPrice:
    def test_returns_price_data(self, mock_ticker):
        result = get_stock_price(mock_ticker)

        assert isinstance(result, PriceData)
        assert result.current == 150.0
        assert result.currency == "USD"
        assert result.high_52w == 180.0
        assert result.low_52w == 120.0

    def test_calculates_change_percentages(self, mock_ticker):
        result = get_stock_price(mock_ticker)

        assert result.change_percent_1d is not None
        assert result.change_percent_1w is not None
        assert result.change_percent_1m is not None

    def test_raises_for_invalid_ticker(self):
        ticker = MagicMock()
        ticker.ticker = "INVALIDTICKER"
        ticker.info = {}

        with pytest.raises(ValueError, match="No price data found"):
            get_stock_price(ticker)

    def test_handles_empty_history(self, mock_stock_info):
        ticker = MagicMock()
        ticker.ticker = "AAPL"
        ticker.info = mock_stock_info
        ticker.history.return_value = pd.DataFrame()

        result = get_stock_price(ticker)

        assert result.current == 150.0
        assert result.change_percent_1d is None
        assert result.change_percent_1w is None
        assert result.change_percent_1m is None


class TestGetPriceHistory:
    def test_returns_dataframe(self, mock_ticker):
        result = get_price_history(mock_ticker)

        assert isinstance(result, pd.DataFrame)
        assert "Open" in result.columns
        assert "High" in result.columns
        assert "Low" in result.columns
        assert "Close" in result.columns
        assert "Volume" in result.columns
        assert len(result) == 30

    def test_raises_for_empty_history(self):
        ticker = MagicMock()
        ticker.ticker = "INVALIDTICKER"
        ticker.history.return_value = pd.DataFrame()

        with pytest.raises(ValueError, match="No price history found"):
            get_price_history(ticker)


class TestGetCompanyName:
    def test_returns_long_name(self, mock_ticker):
        result = get_company_name(mock_ticker)

        assert result == "Apple Inc."

    def test_falls_back_to_short_name(self):
        ticker = MagicMock()
        ticker.info = {"shortName": "AAPL"}

        result = get_company_name(ticker)

        assert result == "AAPL"

    def test_returns_none_for_missing_name(self):
        ticker = MagicMock()
        ticker.info = {}

        result = get_company_name(ticker)

        assert result is None
