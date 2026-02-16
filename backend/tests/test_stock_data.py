from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from app.agents.tools.stock_data import (
    get_company_name,
    get_price_history,
    get_stock_price,
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


class TestGetStockPrice:
    @patch("app.agents.tools.stock_data.yf.Ticker")
    def test_returns_price_data(self, mock_ticker_cls, mock_stock_info, mock_price_history):
        mock_ticker = MagicMock()
        mock_ticker.info = mock_stock_info
        mock_ticker.history.return_value = mock_price_history
        mock_ticker_cls.return_value = mock_ticker

        result = get_stock_price("AAPL")

        assert isinstance(result, PriceData)
        assert result.current == 150.0
        assert result.currency == "USD"
        assert result.high_52w == 180.0
        assert result.low_52w == 120.0

    @patch("app.agents.tools.stock_data.yf.Ticker")
    def test_calculates_change_percentages(self, mock_ticker_cls, mock_stock_info, mock_price_history):
        mock_ticker = MagicMock()
        mock_ticker.info = mock_stock_info
        mock_ticker.history.return_value = mock_price_history
        mock_ticker_cls.return_value = mock_ticker

        result = get_stock_price("AAPL")

        assert result.change_percent_1d is not None
        assert result.change_percent_1w is not None
        assert result.change_percent_1m is not None

    @patch("app.agents.tools.stock_data.yf.Ticker")
    def test_raises_for_invalid_ticker(self, mock_ticker_cls):
        mock_ticker = MagicMock()
        mock_ticker.info = {}
        mock_ticker_cls.return_value = mock_ticker

        with pytest.raises(ValueError, match="No price data found"):
            get_stock_price("INVALIDTICKER")

    @patch("app.agents.tools.stock_data.yf.Ticker")
    def test_handles_empty_history(self, mock_ticker_cls, mock_stock_info):
        mock_ticker = MagicMock()
        mock_ticker.info = mock_stock_info
        mock_ticker.history.return_value = pd.DataFrame()
        mock_ticker_cls.return_value = mock_ticker

        result = get_stock_price("AAPL")

        assert result.current == 150.0
        assert result.change_percent_1d is None
        assert result.change_percent_1w is None
        assert result.change_percent_1m is None


class TestGetPriceHistory:
    @patch("app.agents.tools.stock_data.yf.Ticker")
    def test_returns_dataframe(self, mock_ticker_cls, mock_price_history):
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = mock_price_history
        mock_ticker_cls.return_value = mock_ticker

        result = get_price_history("AAPL")

        assert isinstance(result, pd.DataFrame)
        assert "Open" in result.columns
        assert "High" in result.columns
        assert "Low" in result.columns
        assert "Close" in result.columns
        assert "Volume" in result.columns
        assert len(result) == 30

    @patch("app.agents.tools.stock_data.yf.Ticker")
    def test_raises_for_empty_history(self, mock_ticker_cls):
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = pd.DataFrame()
        mock_ticker_cls.return_value = mock_ticker

        with pytest.raises(ValueError, match="No price history found"):
            get_price_history("INVALIDTICKER")


class TestGetCompanyName:
    @patch("app.agents.tools.stock_data.yf.Ticker")
    def test_returns_long_name(self, mock_ticker_cls, mock_stock_info):
        mock_ticker = MagicMock()
        mock_ticker.info = mock_stock_info
        mock_ticker_cls.return_value = mock_ticker

        result = get_company_name("AAPL")

        assert result == "Apple Inc."

    @patch("app.agents.tools.stock_data.yf.Ticker")
    def test_falls_back_to_short_name(self, mock_ticker_cls):
        mock_ticker = MagicMock()
        mock_ticker.info = {"shortName": "AAPL"}
        mock_ticker_cls.return_value = mock_ticker

        result = get_company_name("AAPL")

        assert result == "AAPL"

    @patch("app.agents.tools.stock_data.yf.Ticker")
    def test_returns_none_for_missing_name(self, mock_ticker_cls):
        mock_ticker = MagicMock()
        mock_ticker.info = {}
        mock_ticker_cls.return_value = mock_ticker

        result = get_company_name("UNKNOWN")

        assert result is None
