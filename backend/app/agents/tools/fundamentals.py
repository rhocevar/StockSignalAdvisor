from typing import Callable

import yfinance as yf

from app.models.domain import FundamentalAnalysis, FundamentalInterpretation

# Centralized mapping: (yfinance_info_key, FundamentalAnalysis_field_name)
# To add a new metric, add a tuple here — the fetch function loops over this.
_YFINANCE_FIELD_MAP: list[tuple[str, str]] = [
    # Valuation
    ("trailingPE", "pe_ratio"),
    ("forwardPE", "forward_pe"),
    ("pegRatio", "peg_ratio"),
    ("priceToBook", "price_to_book"),
    ("priceToSalesTrailing12Months", "price_to_sales"),
    ("enterpriseToEbitda", "enterprise_to_ebitda"),
    # Profitability
    ("profitMargins", "profit_margin"),
    ("operatingMargins", "operating_margin"),
    ("grossMargins", "gross_margin"),
    ("returnOnEquity", "return_on_equity"),
    ("returnOnAssets", "return_on_assets"),
    # Growth
    ("revenueGrowth", "revenue_growth"),
    ("earningsGrowth", "earnings_growth"),
    ("earningsQuarterlyGrowth", "earnings_quarterly_growth"),
    # Financial Health
    ("currentRatio", "current_ratio"),
    ("debtToEquity", "debt_to_equity"),
    ("freeCashflow", "free_cash_flow"),
    ("operatingCashflow", "operating_cash_flow"),
    # Dividends
    ("dividendYield", "dividend_yield"),
    ("payoutRatio", "dividend_payout_ratio"),
    # Size & Market
    ("marketCap", "market_cap"),
    ("enterpriseValue", "enterprise_value"),
    ("sharesOutstanding", "shares_outstanding"),
    ("floatShares", "float_shares"),
    # Analyst
    ("targetMeanPrice", "analyst_target"),
    ("recommendationMean", "analyst_rating"),
    ("numberOfAnalystOpinions", "number_of_analysts"),
]

# Fields needing transformation after extraction from yfinance.
# yfinance returns debtToEquity as a percentage (e.g. 180 = 1.80x).
# yfinance >=1.0 returns dividendYield as a percentage (e.g. 0.41 = 0.41%).
_FIELD_TRANSFORMS: dict[str, Callable[[float], float | None]] = {
    "debt_to_equity": lambda v: v / 100.0,
    "dividend_yield": lambda v: v / 100.0,
}


def get_fundamental_metrics(stock: yf.Ticker) -> FundamentalAnalysis:
    """Fetch fundamental metrics from a shared yf.Ticker instance."""
    info = stock.info

    if not info or info.get("marketCap") is None:
        raise ValueError(f"No fundamental data found for ticker: {stock.ticker}")

    data: dict = {}
    for yf_key, field_name in _YFINANCE_FIELD_MAP:
        value = info.get(yf_key)
        if value is not None and field_name in _FIELD_TRANSFORMS:
            value = _FIELD_TRANSFORMS[field_name](value)
        data[field_name] = value

    return FundamentalAnalysis(**data)


def _score_valuation(metrics: FundamentalAnalysis) -> tuple[float, int, list[str]]:
    """Score valuation metrics. Returns (raw_score, factor_count, insights)."""
    score = 0.0
    factors = 0
    insights: list[str] = []

    if metrics.pe_ratio is not None:
        factors += 1
        if metrics.pe_ratio < 15:
            score += 1.0
            insights.append(f"P/E ratio of {metrics.pe_ratio:.1f} suggests undervaluation")
        elif metrics.pe_ratio > 30:
            score += 0.0
            insights.append(f"P/E ratio of {metrics.pe_ratio:.1f} suggests overvaluation")
        else:
            score += 1.0 - (metrics.pe_ratio - 15) / 15.0
            insights.append(f"P/E ratio of {metrics.pe_ratio:.1f} is moderate")

    if metrics.peg_ratio is not None:
        factors += 1
        if metrics.peg_ratio < 1:
            score += 1.0
            insights.append(f"PEG ratio of {metrics.peg_ratio:.2f} indicates growth at a reasonable price")
        elif metrics.peg_ratio > 2:
            score += 0.0
            insights.append(f"PEG ratio of {metrics.peg_ratio:.2f} suggests overvaluation relative to growth")
        else:
            score += 1.0 - (metrics.peg_ratio - 1.0)
            insights.append(f"PEG ratio of {metrics.peg_ratio:.2f} is moderate")

    return score, factors, insights


def _score_profitability(metrics: FundamentalAnalysis) -> tuple[float, int, list[str]]:
    """Score profitability metrics."""
    score = 0.0
    factors = 0
    insights: list[str] = []

    if metrics.profit_margin is not None:
        factors += 1
        margin_pct = metrics.profit_margin * 100
        if metrics.profit_margin > 0.20:
            score += 1.0
            insights.append(f"Profit margin of {margin_pct:.1f}% is strong")
        elif metrics.profit_margin < 0.05:
            score += 0.0
            insights.append(f"Profit margin of {margin_pct:.1f}% is weak")
        else:
            score += (metrics.profit_margin - 0.05) / 0.15
            insights.append(f"Profit margin of {margin_pct:.1f}% is moderate")

    if metrics.return_on_equity is not None:
        factors += 1
        roe_pct = metrics.return_on_equity * 100
        if metrics.return_on_equity > 0.15:
            score += 1.0
            insights.append(f"ROE of {roe_pct:.1f}% indicates efficient use of equity")
        elif metrics.return_on_equity < 0.05:
            score += 0.0
            insights.append(f"ROE of {roe_pct:.1f}% is below average")
        else:
            score += (metrics.return_on_equity - 0.05) / 0.10
            insights.append(f"ROE of {roe_pct:.1f}% is moderate")

    return score, factors, insights


def _score_growth(metrics: FundamentalAnalysis) -> tuple[float, int, list[str]]:
    """Score growth metrics."""
    score = 0.0
    factors = 0
    insights: list[str] = []

    if metrics.revenue_growth is not None:
        factors += 1
        growth_pct = metrics.revenue_growth * 100
        if metrics.revenue_growth > 0.15:
            score += 1.0
            insights.append(f"Revenue growth of {growth_pct:.1f}% is strong")
        elif metrics.revenue_growth < 0:
            score += 0.0
            insights.append(f"Revenue declining at {growth_pct:.1f}%")
        else:
            score += metrics.revenue_growth / 0.15
            insights.append(f"Revenue growth of {growth_pct:.1f}% is moderate")

    if metrics.earnings_growth is not None:
        factors += 1
        growth_pct = metrics.earnings_growth * 100
        if metrics.earnings_growth > 0.20:
            score += 1.0
            insights.append(f"Earnings growth of {growth_pct:.1f}% is strong")
        elif metrics.earnings_growth < 0:
            score += 0.0
            insights.append(f"Earnings declining at {growth_pct:.1f}%")
        else:
            score += metrics.earnings_growth / 0.20
            insights.append(f"Earnings growth of {growth_pct:.1f}% is moderate")

    return score, factors, insights


def _score_financial_health(metrics: FundamentalAnalysis) -> tuple[float, int, list[str]]:
    """Score financial health metrics."""
    score = 0.0
    factors = 0
    insights: list[str] = []

    if metrics.debt_to_equity is not None:
        factors += 1
        if metrics.debt_to_equity < 0.5:
            score += 1.0
            insights.append(f"Low debt-to-equity of {metrics.debt_to_equity:.2f} indicates conservative financing")
        elif metrics.debt_to_equity > 2.0:
            score += 0.0
            insights.append(f"High debt-to-equity of {metrics.debt_to_equity:.2f} signals leverage risk")
        else:
            score += 1.0 - (metrics.debt_to_equity - 0.5) / 1.5
            insights.append(f"Debt-to-equity of {metrics.debt_to_equity:.2f} is moderate")

    if metrics.current_ratio is not None:
        factors += 1
        if metrics.current_ratio > 1.5:
            score += 1.0
            insights.append(f"Current ratio of {metrics.current_ratio:.2f} shows strong liquidity")
        elif metrics.current_ratio < 1.0:
            score += 0.0
            insights.append(f"Current ratio of {metrics.current_ratio:.2f} indicates liquidity concern")
        else:
            score += (metrics.current_ratio - 1.0) / 0.5
            insights.append(f"Current ratio of {metrics.current_ratio:.2f} is adequate")

    if metrics.free_cash_flow is not None:
        factors += 1
        if metrics.free_cash_flow > 0:
            score += 1.0
            insights.append("Positive free cash flow supports financial flexibility")
        else:
            score += 0.0
            insights.append("Negative free cash flow may limit financial flexibility")

    return score, factors, insights


def interpret_fundamentals(metrics: FundamentalAnalysis) -> FundamentalInterpretation:
    """Interpret fundamental metrics into a score and insights.

    Score is 0.0 (bearish) to 1.0 (bullish), with equal 25% weight per category.
    """
    categories = [
        _score_valuation(metrics),
        _score_profitability(metrics),
        _score_growth(metrics),
        _score_financial_health(metrics),
    ]

    total_score = 0.0
    all_insights: list[str] = []

    for cat_score, cat_factors, cat_insights in categories:
        if cat_factors > 0:
            total_score += 0.25 * (cat_score / cat_factors)
        all_insights.extend(cat_insights)

    total_factors = sum(factors for _, factors, _ in categories)
    if total_factors == 0:
        total_score = 0.5  # Neutral when no data available

    return FundamentalInterpretation(
        score=round(total_score, 4),
        insights=all_insights,
    )


def calculate_fundamentals(stock: yf.Ticker) -> FundamentalAnalysis:
    """Orchestrator: fetch fundamental metrics, interpret, and return scored analysis."""
    metrics = get_fundamental_metrics(stock)
    interpretation = interpret_fundamentals(metrics)

    metrics.fundamental_score = interpretation.score
    metrics.insights = interpretation.insights

    return metrics
