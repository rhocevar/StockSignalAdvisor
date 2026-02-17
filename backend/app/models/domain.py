from datetime import datetime

from pydantic import BaseModel

from app.enums import (
    MacdSignal,
    SentimentType,
    SignalType,
    TrendDirection,
    VolumeTrend,
)


class TechnicalAnalysis(BaseModel):
    rsi: float | None = None
    rsi_interpretation: str | None = None
    sma_50: float | None = None
    sma_200: float | None = None
    price_vs_sma50: TrendDirection | None = None
    price_vs_sma200: TrendDirection | None = None
    macd_signal: MacdSignal | None = None
    volume_trend: VolumeTrend | None = None
    technical_score: float | None = None


class FundamentalAnalysis(BaseModel):
    # Valuation
    pe_ratio: float | None = None
    forward_pe: float | None = None
    peg_ratio: float | None = None
    price_to_book: float | None = None
    price_to_sales: float | None = None
    enterprise_to_ebitda: float | None = None

    # Profitability
    profit_margin: float | None = None
    operating_margin: float | None = None
    gross_margin: float | None = None
    return_on_equity: float | None = None
    return_on_assets: float | None = None

    # Growth
    revenue_growth: float | None = None
    earnings_growth: float | None = None
    earnings_quarterly_growth: float | None = None

    # Financial Health
    current_ratio: float | None = None
    debt_to_equity: float | None = None
    free_cash_flow: float | None = None
    operating_cash_flow: float | None = None

    # Dividends
    dividend_yield: float | None = None
    dividend_payout_ratio: float | None = None

    # Size & Market
    market_cap: float | None = None
    enterprise_value: float | None = None
    shares_outstanding: float | None = None
    float_shares: float | None = None

    # Analyst
    analyst_target: float | None = None
    analyst_rating: float | None = None
    number_of_analysts: int | None = None

    # Derived
    fundamental_score: float | None = None
    insights: list[str] = []


class FundamentalInterpretation(BaseModel):
    score: float  # 0.0 (bearish) to 1.0 (bullish)
    insights: list[str] = []


class SentimentAnalysis(BaseModel):
    overall: SentimentType | None = None
    score: float | None = None
    positive_count: int = 0
    negative_count: int = 0
    neutral_count: int = 0


class AnalysisResult(BaseModel):
    technical: TechnicalAnalysis | None = None
    fundamentals: FundamentalAnalysis | None = None
    sentiment: SentimentAnalysis | None = None


class PriceData(BaseModel):
    current: float | None = None
    currency: str = "USD"
    change_percent_1d: float | None = None
    change_percent_1w: float | None = None
    change_percent_1m: float | None = None
    high_52w: float | None = None
    low_52w: float | None = None


class NewsSource(BaseModel):
    type: str = "news"
    title: str
    source: str | None = None
    url: str | None = None
    sentiment: SentimentType | None = None
    published_at: datetime | None = None


class AnalysisMetadata(BaseModel):
    model_config = {"protected_namespaces": ()}

    generated_at: datetime
    llm_provider: str
    model_used: str
    vectorstore_provider: str
    cached: bool = False
