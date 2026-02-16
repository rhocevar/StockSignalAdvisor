from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.enums import (
    MacdSignal,
    SentimentType,
    SignalType,
    TrendDirection,
    VolumeTrend,
)


class TechnicalAnalysis(BaseModel):
    rsi: Optional[float] = None
    rsi_interpretation: Optional[str] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    price_vs_sma50: Optional[TrendDirection] = None
    price_vs_sma200: Optional[TrendDirection] = None
    macd_signal: Optional[MacdSignal] = None
    volume_trend: Optional[VolumeTrend] = None
    technical_score: Optional[float] = None


class FundamentalAnalysis(BaseModel):
    # Valuation
    pe_ratio: Optional[float] = None
    forward_pe: Optional[float] = None
    peg_ratio: Optional[float] = None
    price_to_book: Optional[float] = None
    price_to_sales: Optional[float] = None
    enterprise_to_ebitda: Optional[float] = None

    # Profitability
    profit_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    gross_margin: Optional[float] = None
    return_on_equity: Optional[float] = None
    return_on_assets: Optional[float] = None

    # Growth
    revenue_growth: Optional[float] = None
    earnings_growth: Optional[float] = None
    earnings_quarterly_growth: Optional[float] = None

    # Financial Health
    current_ratio: Optional[float] = None
    debt_to_equity: Optional[float] = None
    free_cash_flow: Optional[float] = None
    operating_cash_flow: Optional[float] = None

    # Dividends
    dividend_yield: Optional[float] = None
    dividend_payout_ratio: Optional[float] = None

    # Size & Market
    market_cap: Optional[float] = None
    enterprise_value: Optional[float] = None
    shares_outstanding: Optional[float] = None
    float_shares: Optional[float] = None

    # Analyst
    analyst_target: Optional[float] = None
    analyst_rating: Optional[float] = None
    number_of_analysts: Optional[int] = None

    # Derived
    fundamental_score: Optional[float] = None
    insights: list[str] = []


class FundamentalInterpretation(BaseModel):
    score: float  # 0.0 (bearish) to 1.0 (bullish)
    insights: list[str] = []


class SentimentAnalysis(BaseModel):
    overall: Optional[SentimentType] = None
    score: Optional[float] = None
    positive_count: int = 0
    negative_count: int = 0
    neutral_count: int = 0


class AnalysisResult(BaseModel):
    technical: Optional[TechnicalAnalysis] = None
    fundamentals: Optional[FundamentalAnalysis] = None
    sentiment: Optional[SentimentAnalysis] = None


class PriceData(BaseModel):
    current: Optional[float] = None
    currency: str = "USD"
    change_percent_1d: Optional[float] = None
    change_percent_1w: Optional[float] = None
    change_percent_1m: Optional[float] = None
    high_52w: Optional[float] = None
    low_52w: Optional[float] = None


class NewsSource(BaseModel):
    type: str = "news"
    title: str
    source: Optional[str] = None
    url: Optional[str] = None
    sentiment: Optional[SentimentType] = None
    published_at: Optional[datetime] = None


class AnalysisMetadata(BaseModel):
    model_config = {"protected_namespaces": ()}

    generated_at: datetime
    llm_provider: str
    model_used: str
    vectorstore_provider: str
    cached: bool = False
