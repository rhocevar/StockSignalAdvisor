from datetime import datetime, timedelta, timezone

import pandas as pd
import yfinance as yf

from app.models.domain import PriceData, PricePoint

_YF_TIMEOUT_SECONDS = 10


def get_ticker(ticker: str) -> yf.Ticker:
    """Create a yf.Ticker instance. The orchestrator calls this once and shares it."""
    return yf.Ticker(ticker)


def get_stock_price(stock: yf.Ticker) -> PriceData:
    """Fetch current price data using a shared yf.Ticker instance."""
    info = stock.info

    if not info or info.get("regularMarketPrice") is None:
        raise ValueError(f"No price data found for ticker: {stock.ticker}")

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

    price_history: list[PricePoint] | None = None
    if not history.empty:
        points = [
            PricePoint(date=d.strftime("%Y-%m-%d"), close=round(float(c), 4))
            for d, c in zip(history.index, history["Close"])
            if pd.notna(c)
        ]
        price_history = points if points else None

    return PriceData(
        current=current_price,
        currency=info.get("currency", "USD"),
        change_percent_1d=change_1d,
        change_percent_1w=change_1w,
        change_percent_1m=change_1m,
        high_52w=info.get("fiftyTwoWeekHigh"),
        low_52w=info.get("fiftyTwoWeekLow"),
        price_history=price_history,
    )


def get_price_history(stock: yf.Ticker, period: str = "1y") -> pd.DataFrame:
    """Fetch OHLCV price history using a shared yf.Ticker instance."""
    history = stock.history(period=period, timeout=_YF_TIMEOUT_SECONDS)

    if history.empty:
        raise ValueError(f"No price history found for ticker: {stock.ticker}")

    return history


def get_company_name(stock: yf.Ticker) -> str | None:
    """Extract company name from yfinance ticker info."""
    info = stock.info
    if not info:
        return None
    return info.get("longName") or info.get("shortName")
