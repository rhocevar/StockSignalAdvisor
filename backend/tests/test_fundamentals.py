from unittest.mock import MagicMock

import pytest

from app.agents.tools.fundamentals import (
    _YFINANCE_FIELD_MAP,
    calculate_fundamentals,
    get_fundamental_metrics,
    interpret_fundamentals,
)
from app.models.domain import FundamentalAnalysis, FundamentalInterpretation


@pytest.fixture
def mock_yfinance_info():
    """Complete yfinance info dict for a healthy company."""
    return {
        "marketCap": 3000000000000,
        "trailingPE": 28.5,
        "forwardPE": 25.0,
        "pegRatio": 1.5,
        "priceToBook": 40.0,
        "priceToSalesTrailing12Months": 7.5,
        "enterpriseToEbitda": 22.0,
        "profitMargins": 0.25,
        "operatingMargins": 0.30,
        "grossMargins": 0.45,
        "returnOnEquity": 0.18,
        "returnOnAssets": 0.12,
        "revenueGrowth": 0.08,
        "earningsGrowth": 0.15,
        "earningsQuarterlyGrowth": 0.10,
        "currentRatio": 1.1,
        "debtToEquity": 180.0,  # yfinance returns as percentage
        "freeCashflow": 100000000000,
        "operatingCashflow": 120000000000,
        "dividendYield": 0.5,  # yfinance >=1.0 returns as percentage (0.5 = 0.5%)
        "payoutRatio": 0.15,
        "enterpriseValue": 3100000000000,
        "sharesOutstanding": 15000000000,
        "floatShares": 14900000000,
        "targetMeanPrice": 200.0,
        "recommendationMean": 2.0,
        "numberOfAnalystOpinions": 40,
    }


@pytest.fixture
def mock_ticker(mock_yfinance_info):
    """Create a mock yf.Ticker with info pre-configured."""
    ticker = MagicMock()
    ticker.ticker = "AAPL"
    ticker.info = mock_yfinance_info
    return ticker


# ---- Field Mapping Tests ----

class TestFieldMapping:
    def test_all_mapping_fields_exist_on_model(self):
        """Every field in _YFINANCE_FIELD_MAP must be a valid FundamentalAnalysis field."""
        model_fields = set(FundamentalAnalysis.model_fields.keys())
        for _, field_name in _YFINANCE_FIELD_MAP:
            assert field_name in model_fields, f"Mapping references unknown field: {field_name}"

    def test_mapping_has_no_duplicate_model_fields(self):
        """No model field should be mapped twice."""
        field_names = [field_name for _, field_name in _YFINANCE_FIELD_MAP]
        assert len(field_names) == len(set(field_names)), "Duplicate model field in mapping"

    def test_mapping_has_no_duplicate_yfinance_keys(self):
        """No yfinance key should appear twice."""
        yf_keys = [yf_key for yf_key, _ in _YFINANCE_FIELD_MAP]
        assert len(yf_keys) == len(set(yf_keys)), "Duplicate yfinance key in mapping"


# ---- get_fundamental_metrics Tests ----

class TestGetFundamentalMetrics:
    def test_maps_all_fields(self, mock_ticker):
        result = get_fundamental_metrics(mock_ticker)

        assert isinstance(result, FundamentalAnalysis)
        assert result.pe_ratio == 28.5
        assert result.forward_pe == 25.0
        assert result.peg_ratio == 1.5
        assert result.profit_margin == 0.25
        assert result.return_on_equity == 0.18
        assert result.revenue_growth == 0.08
        assert result.market_cap == 3000000000000
        assert result.analyst_target == 200.0
        assert result.number_of_analysts == 40

    def test_debt_to_equity_divided_by_100(self, mock_ticker):
        result = get_fundamental_metrics(mock_ticker)

        assert result.debt_to_equity == 1.80  # 180 / 100

    def test_handles_missing_fields(self):
        ticker = MagicMock()
        ticker.ticker = "SMALL"
        ticker.info = {"marketCap": 1000000}

        result = get_fundamental_metrics(ticker)

        assert result.pe_ratio is None
        assert result.profit_margin is None
        assert result.revenue_growth is None
        assert result.market_cap == 1000000

    def test_raises_for_invalid_ticker(self):
        ticker = MagicMock()
        ticker.ticker = "INVALIDTICKER"
        ticker.info = {}

        with pytest.raises(ValueError, match="No fundamental data found"):
            get_fundamental_metrics(ticker)


# ---- interpret_fundamentals Tests ----

class TestInterpretFundamentalsValuation:
    def test_low_pe_scores_well(self):
        metrics = FundamentalAnalysis(pe_ratio=12.0)
        result = interpret_fundamentals(metrics)
        assert isinstance(result, FundamentalInterpretation)
        assert result.score > 0.2  # 25% weight, full score

    def test_high_pe_scores_poorly(self):
        metrics = FundamentalAnalysis(pe_ratio=35.0)
        result = interpret_fundamentals(metrics)
        assert result.score < 0.05

    def test_low_peg_scores_well(self):
        metrics = FundamentalAnalysis(peg_ratio=0.8)
        result = interpret_fundamentals(metrics)
        assert result.score > 0.2

    def test_high_peg_scores_poorly(self):
        metrics = FundamentalAnalysis(peg_ratio=3.0)
        result = interpret_fundamentals(metrics)
        assert result.score < 0.05


class TestInterpretFundamentalsProfitability:
    def test_high_margin_scores_well(self):
        metrics = FundamentalAnalysis(profit_margin=0.25)
        result = interpret_fundamentals(metrics)
        assert result.score > 0.2

    def test_low_margin_scores_poorly(self):
        metrics = FundamentalAnalysis(profit_margin=0.02)
        result = interpret_fundamentals(metrics)
        assert result.score < 0.05

    def test_high_roe_scores_well(self):
        metrics = FundamentalAnalysis(return_on_equity=0.20)
        result = interpret_fundamentals(metrics)
        assert result.score > 0.2

    def test_low_roe_scores_poorly(self):
        metrics = FundamentalAnalysis(return_on_equity=0.03)
        result = interpret_fundamentals(metrics)
        assert result.score < 0.05


class TestInterpretFundamentalsGrowth:
    def test_strong_revenue_growth(self):
        metrics = FundamentalAnalysis(revenue_growth=0.20)
        result = interpret_fundamentals(metrics)
        assert result.score > 0.2

    def test_negative_revenue_growth(self):
        metrics = FundamentalAnalysis(revenue_growth=-0.10)
        result = interpret_fundamentals(metrics)
        assert result.score < 0.05

    def test_strong_earnings_growth(self):
        metrics = FundamentalAnalysis(earnings_growth=0.25)
        result = interpret_fundamentals(metrics)
        assert result.score > 0.2

    def test_negative_earnings_growth(self):
        metrics = FundamentalAnalysis(earnings_growth=-0.05)
        result = interpret_fundamentals(metrics)
        assert result.score < 0.05


class TestInterpretFundamentalsFinancialHealth:
    def test_low_debt_scores_well(self):
        metrics = FundamentalAnalysis(debt_to_equity=0.3)
        result = interpret_fundamentals(metrics)
        assert result.score > 0.2

    def test_high_debt_scores_poorly(self):
        metrics = FundamentalAnalysis(debt_to_equity=3.0)
        result = interpret_fundamentals(metrics)
        assert result.score < 0.05

    def test_strong_liquidity(self):
        metrics = FundamentalAnalysis(current_ratio=2.0)
        result = interpret_fundamentals(metrics)
        assert result.score > 0.2

    def test_weak_liquidity(self):
        metrics = FundamentalAnalysis(current_ratio=0.7)
        result = interpret_fundamentals(metrics)
        assert result.score < 0.05

    def test_positive_fcf(self):
        metrics = FundamentalAnalysis(free_cash_flow=5000000)
        result = interpret_fundamentals(metrics)
        assert result.score > 0.2

    def test_negative_fcf(self):
        metrics = FundamentalAnalysis(free_cash_flow=-1000000)
        result = interpret_fundamentals(metrics)
        assert result.score < 0.05


class TestInterpretFundamentalsInsights:
    def test_generates_insights(self):
        metrics = FundamentalAnalysis(
            pe_ratio=12.0,
            profit_margin=0.25,
            revenue_growth=0.20,
            debt_to_equity=0.3,
        )
        result = interpret_fundamentals(metrics)
        assert len(result.insights) >= 4

    def test_no_data_returns_neutral(self):
        metrics = FundamentalAnalysis()
        result = interpret_fundamentals(metrics)
        assert result.score == 0.5
        assert len(result.insights) == 0


class TestInterpretFundamentalsScoreRange:
    def test_bullish_company(self):
        metrics = FundamentalAnalysis(
            pe_ratio=10.0,
            peg_ratio=0.5,
            profit_margin=0.30,
            return_on_equity=0.25,
            revenue_growth=0.20,
            earnings_growth=0.30,
            debt_to_equity=0.2,
            current_ratio=2.5,
            free_cash_flow=10000000,
        )
        result = interpret_fundamentals(metrics)
        assert result.score > 0.8

    def test_bearish_company(self):
        metrics = FundamentalAnalysis(
            pe_ratio=50.0,
            peg_ratio=4.0,
            profit_margin=0.01,
            return_on_equity=0.02,
            revenue_growth=-0.15,
            earnings_growth=-0.20,
            debt_to_equity=5.0,
            current_ratio=0.5,
            free_cash_flow=-5000000,
        )
        result = interpret_fundamentals(metrics)
        assert result.score < 0.1

    def test_score_always_in_range(self):
        metrics = FundamentalAnalysis(
            pe_ratio=20.0,
            profit_margin=0.10,
            revenue_growth=0.05,
            debt_to_equity=1.0,
        )
        result = interpret_fundamentals(metrics)
        assert 0.0 <= result.score <= 1.0


# ---- calculate_fundamentals End-to-End Test ----

class TestCalculateFundamentals:
    def test_returns_scored_analysis(self, mock_ticker):
        result = calculate_fundamentals(mock_ticker)

        assert isinstance(result, FundamentalAnalysis)
        assert result.fundamental_score is not None
        assert 0.0 <= result.fundamental_score <= 1.0
        assert len(result.insights) > 0
        assert result.pe_ratio == 28.5
        assert result.market_cap == 3000000000000
