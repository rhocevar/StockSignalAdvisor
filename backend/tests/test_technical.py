from unittest.mock import patch

import pandas as pd
import pytest

from app.enums import MacdSignal, TrendDirection, VolumeTrend
from app.models.domain import TechnicalAnalysis

from app.agents.tools.technical import (
    assess_volume_trend,
    calculate_macd,
    calculate_rsi,
    calculate_sma,
    calculate_technical_score,
    calculate_technicals,
    interpret_macd,
    interpret_rsi,
)


# ---- Fixtures ----

@pytest.fixture
def rising_prices():
    """Steadily rising prices over 50 days."""
    return pd.Series([100 + i for i in range(50)])


@pytest.fixture
def falling_prices():
    """Steadily falling prices over 50 days."""
    return pd.Series([150 - i for i in range(50)])


@pytest.fixture
def stable_prices():
    """Prices oscillating around 100 over 250 days."""
    return pd.Series([100 + (i % 3 - 1) * 0.5 for i in range(250)])


@pytest.fixture
def mock_history():
    """A full year of mock OHLCV data for end-to-end testing."""
    n = 252
    dates = pd.date_range(end="2024-01-30", periods=n, freq="B")
    closes = [150 + i * 0.1 for i in range(n)]
    return pd.DataFrame(
        {
            "Open": [c - 0.5 for c in closes],
            "High": [c + 1.0 for c in closes],
            "Low": [c - 1.0 for c in closes],
            "Close": closes,
            "Volume": [1000000] * n,
        },
        index=dates,
    )


# ---- RSI Tests ----

class TestCalculateRsi:
    def test_rising_prices_high_rsi(self, rising_prices):
        rsi = calculate_rsi(rising_prices)
        assert rsi is not None
        assert rsi > 70  # Strong uptrend should be overbought

    def test_falling_prices_low_rsi(self, falling_prices):
        rsi = calculate_rsi(falling_prices)
        assert rsi is not None
        assert rsi < 30  # Strong downtrend should be oversold

    def test_insufficient_data_returns_none(self):
        short = pd.Series([100, 101, 102])
        assert calculate_rsi(short, period=14) is None

    def test_all_gains_returns_100(self):
        prices = pd.Series([100 + i for i in range(20)])
        rsi = calculate_rsi(prices, period=14)
        assert rsi == 100.0

    def test_all_losses(self):
        prices = pd.Series([120 - i for i in range(20)])
        rsi = calculate_rsi(prices, period=14)
        assert rsi is not None
        assert rsi < 5  # Should be very low


class TestInterpretRsi:
    def test_oversold(self):
        assert interpret_rsi(25.0) == "oversold"

    def test_overbought(self):
        assert interpret_rsi(75.0) == "overbought"

    def test_neutral(self):
        assert interpret_rsi(50.0) == "neutral"

    def test_boundary_30(self):
        assert interpret_rsi(30.0) == "neutral"

    def test_boundary_70(self):
        assert interpret_rsi(70.0) == "neutral"


# ---- SMA Tests ----

class TestCalculateSma:
    def test_known_values(self):
        prices = pd.Series([10.0, 20.0, 30.0, 40.0, 50.0])
        sma = calculate_sma(prices, period=5)
        assert sma == 30.0

    def test_period_3(self):
        prices = pd.Series([10.0, 20.0, 30.0, 40.0, 50.0])
        sma = calculate_sma(prices, period=3)
        assert sma == 40.0  # avg of last 3: 30, 40, 50

    def test_insufficient_data_returns_none(self):
        prices = pd.Series([10.0, 20.0])
        assert calculate_sma(prices, period=5) is None


# ---- MACD Tests ----

class TestCalculateMacd:
    def test_returns_three_values(self, stable_prices):
        macd_line, signal_line, histogram = calculate_macd(stable_prices)
        assert macd_line is not None
        assert signal_line is not None
        assert histogram is not None

    def test_insufficient_data_returns_nones(self):
        short = pd.Series([100 + i for i in range(10)])
        result = calculate_macd(short)
        assert result == (None, None, None)

    def test_rising_trend_positive_macd(self, rising_prices):
        # Extend to have enough data for MACD
        extended = pd.Series([50 + i * 0.5 for i in range(100)])
        macd_line, signal_line, _ = calculate_macd(extended)
        assert macd_line is not None
        assert macd_line > 0  # Rising prices produce positive MACD


class TestInterpretMacd:
    def test_bullish(self):
        assert interpret_macd(1.5, 1.0) == MacdSignal.BULLISH

    def test_bearish(self):
        assert interpret_macd(0.5, 1.0) == MacdSignal.BEARISH

    def test_neutral_equal(self):
        assert interpret_macd(1.0, 1.0) == MacdSignal.NEUTRAL

    def test_neutral_none_macd(self):
        assert interpret_macd(None, 1.0) == MacdSignal.NEUTRAL

    def test_neutral_none_signal(self):
        assert interpret_macd(1.0, None) == MacdSignal.NEUTRAL


# ---- Volume Trend Tests ----

class TestAssessVolumeTrend:
    def test_high_volume(self):
        volumes = pd.Series([1000000] * 20 + [2000000])
        assert assess_volume_trend(volumes) == VolumeTrend.HIGH

    def test_low_volume(self):
        volumes = pd.Series([1000000] * 20 + [300000])
        assert assess_volume_trend(volumes) == VolumeTrend.LOW

    def test_neutral_volume(self):
        volumes = pd.Series([1000000] * 21)
        assert assess_volume_trend(volumes) == VolumeTrend.NEUTRAL

    def test_insufficient_data(self):
        volumes = pd.Series([1000000] * 5)
        assert assess_volume_trend(volumes) == VolumeTrend.NEUTRAL


# ---- Technical Score Tests ----

class TestCalculateTechnicalScore:
    def test_max_bullish_score(self):
        score = calculate_technical_score(
            rsi=25.0,
            macd_signal=MacdSignal.BULLISH,
            price_vs_sma50=TrendDirection.ABOVE,
            price_vs_sma200=TrendDirection.ABOVE,
            volume_trend=VolumeTrend.HIGH,
        )
        assert score == 1.0

    def test_max_bearish_score(self):
        score = calculate_technical_score(
            rsi=80.0,
            macd_signal=MacdSignal.BEARISH,
            price_vs_sma50=TrendDirection.BELOW,
            price_vs_sma200=TrendDirection.BELOW,
            volume_trend=VolumeTrend.LOW,
        )
        assert score == 0.0

    def test_neutral_score(self):
        score = calculate_technical_score(
            rsi=50.0,
            macd_signal=MacdSignal.NEUTRAL,
            price_vs_sma50=TrendDirection.ABOVE,
            price_vs_sma200=TrendDirection.BELOW,
            volume_trend=VolumeTrend.NEUTRAL,
        )
        assert 0.0 <= score <= 1.0

    def test_none_rsi_handled(self):
        score = calculate_technical_score(
            rsi=None,
            macd_signal=MacdSignal.BULLISH,
            price_vs_sma50=TrendDirection.ABOVE,
            price_vs_sma200=TrendDirection.ABOVE,
            volume_trend=VolumeTrend.HIGH,
        )
        assert 0.0 <= score <= 1.0

    def test_score_in_range(self):
        score = calculate_technical_score(
            rsi=45.0,
            macd_signal=MacdSignal.BULLISH,
            price_vs_sma50=TrendDirection.BELOW,
            price_vs_sma200=TrendDirection.ABOVE,
            volume_trend=VolumeTrend.NEUTRAL,
        )
        assert 0.0 <= score <= 1.0


# ---- End-to-End Orchestrator Test ----

class TestCalculateTechnicals:
    @patch("app.agents.tools.technical.get_price_history")
    def test_returns_technical_analysis(self, mock_get_history, mock_history):
        mock_get_history.return_value = mock_history

        result = calculate_technicals("AAPL")

        assert isinstance(result, TechnicalAnalysis)
        assert result.rsi is not None
        assert result.sma_50 is not None
        assert result.sma_200 is not None
        assert result.price_vs_sma50 is not None
        assert result.price_vs_sma200 is not None
        assert result.macd_signal is not None
        assert result.volume_trend is not None
        assert result.technical_score is not None
        assert 0.0 <= result.technical_score <= 1.0

    @patch("app.agents.tools.technical.get_price_history")
    def test_rsi_interpretation_set(self, mock_get_history, mock_history):
        mock_get_history.return_value = mock_history

        result = calculate_technicals("AAPL")

        assert result.rsi_interpretation in ("oversold", "overbought", "neutral")
