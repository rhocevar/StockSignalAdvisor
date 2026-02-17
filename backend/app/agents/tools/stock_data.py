from datetime import datetime, timedelta, timezone

import pandas as pd
import yfinance as yf

from app.models.domain import PriceData

# TODO(Day 12): Share a single yf.Ticker instance across stock_data, technical,
# and fundamentals when the orchestrator is built, to avoid redundant API calls.

_YF_TIMEOUT_SECONDS = 10


def get_stock_price(ticker: str) -> PriceData:
    """Fetch current price data for a ticker using yfinance."""
    stock = yf.Ticker(ticker)
    info = stock.info

    if not info or info.get("regularMarketPrice") is None:
        raise ValueError(f"No price data found for ticker: {ticker}")

    current_price = info.get("regularMarketPrice") or info.get("currentPrice")
    history = stock.history(period="1mo", timeout=_YF_TIMEOUT_SECONDS)

    change_1d: float | None = None
    change_1w: float | None = None
    change_1m: float | None = None

    if not history.empty and current_price:
        if len(history) >= 2:
            prev_close = history["Close"].iloc[-2]
            change_1d = round((current_price - prev_close) / prev_close * 100, 2)

        # Find the closest trading day to 7 calendar days ago
        if len(history) >= 2:
            target_date = datetime.now(timezone.utc) - timedelta(days=7)
            # Ensure target_date matches the index timezone
            if history.index.tz is None:
                target_date = target_date.replace(tzinfo=None)
            idx = history.index.get_indexer([target_date], method="ffill")[0]
            if idx >= 0:
                week_ago = history["Close"].iloc[idx]
                change_1w = round((current_price - week_ago) / week_ago * 100, 2)

        if len(history) >= 1:
            month_ago = history["Close"].iloc[0]
            change_1m = round((current_price - month_ago) / month_ago * 100, 2)

    return PriceData(
        current=current_price,
        currency=info.get("currency", "USD"),
        change_percent_1d=change_1d,
        change_percent_1w=change_1w,
        change_percent_1m=change_1m,
        high_52w=info.get("fiftyTwoWeekHigh"),
        low_52w=info.get("fiftyTwoWeekLow"),
    )


def get_price_history(ticker: str, period: str = "1y") -> pd.DataFrame:
    """Fetch OHLCV price history for a ticker."""
    stock = yf.Ticker(ticker)
    history = stock.history(period=period, timeout=_YF_TIMEOUT_SECONDS)

    if history.empty:
        raise ValueError(f"No price history found for ticker: {ticker}")

    return history


def get_company_name(ticker: str) -> str | None:
    """Extract company name from yfinance ticker info."""
    stock = yf.Ticker(ticker)
    info = stock.info
    return info.get("longName") or info.get("shortName")
