import pandas as pd

from app.enums import MacdSignal, TrendDirection, VolumeTrend
from app.models.domain import TechnicalAnalysis

from .stock_data import get_price_history


def calculate_rsi(prices: pd.Series, period: int = 14) -> float | None:
    """Calculate Relative Strength Index (RSI).

    RSI = 100 - (100 / (1 + RS))
    RS = Average Gain / Average Loss over the period.
    """
    if len(prices) < period + 1:
        return None

    deltas = prices.diff()
    gains = deltas.clip(lower=0)
    losses = (-deltas).clip(lower=0)

    avg_gain = gains.iloc[1 : period + 1].mean()
    avg_loss = losses.iloc[1 : period + 1].mean()

    for i in range(period + 1, len(prices)):
        avg_gain = (avg_gain * (period - 1) + gains.iloc[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses.iloc[i]) / period

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return round(rsi, 2)


def interpret_rsi(rsi: float) -> str:
    """Interpret RSI value into a human-readable string."""
    if rsi < 30:
        return "oversold"
    elif rsi > 70:
        return "overbought"
    return "neutral"


def calculate_sma(prices: pd.Series, period: int) -> float | None:
    """Calculate Simple Moving Average."""
    if len(prices) < period:
        return None
    return round(float(prices.iloc[-period:].mean()), 2)


def calculate_macd(
    prices: pd.Series,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> tuple[float | None, float | None, float | None]:
    """Calculate MACD (Moving Average Convergence Divergence).

    Returns (macd_line, signal_line, histogram).
    """
    if len(prices) < slow_period + signal_period:
        return None, None, None

    ema_fast = prices.ewm(span=fast_period, adjust=False).mean()
    ema_slow = prices.ewm(span=slow_period, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    histogram = macd_line - signal_line

    return (
        round(float(macd_line.iloc[-1]), 4),
        round(float(signal_line.iloc[-1]), 4),
        round(float(histogram.iloc[-1]), 4),
    )


def interpret_macd(
    macd_line: float | None, signal_line: float | None
) -> MacdSignal:
    """Interpret MACD crossover into a signal."""
    if macd_line is None or signal_line is None:
        return MacdSignal.NEUTRAL
    if macd_line > signal_line:
        return MacdSignal.BULLISH
    elif macd_line < signal_line:
        return MacdSignal.BEARISH
    return MacdSignal.NEUTRAL


def assess_volume_trend(volumes: pd.Series, window: int = 20) -> VolumeTrend:
    """Assess volume trend by comparing recent volume to average."""
    if len(volumes) < window + 1:
        return VolumeTrend.NEUTRAL

    avg_volume = volumes.iloc[-window - 1 : -1].mean()
    recent_volume = volumes.iloc[-1]

    if avg_volume == 0:
        return VolumeTrend.NEUTRAL

    ratio = recent_volume / avg_volume
    if ratio > 1.5:
        return VolumeTrend.HIGH
    elif ratio < 0.5:
        return VolumeTrend.LOW
    return VolumeTrend.NEUTRAL


def calculate_technical_score(
    rsi: float | None,
    macd_signal: MacdSignal,
    price_vs_sma50: TrendDirection | None,
    price_vs_sma200: TrendDirection | None,
    volume_trend: VolumeTrend,
) -> float:
    """Calculate a composite technical score from 0.0 (bearish) to 1.0 (bullish).

    Weights: RSI 25%, MACD 25%, SMA50 20%, SMA200 20%, Volume 10%.
    """
    score = 0.0

    # RSI component (25%)
    if rsi is not None:
        if rsi < 30:
            score += 0.25  # Oversold = bullish
        elif rsi > 70:
            score += 0.0  # Overbought = bearish
        else:
            score += 0.25 * (1.0 - (rsi - 30) / 40.0)  # Linear scale

    # MACD component (25%)
    if macd_signal == MacdSignal.BULLISH:
        score += 0.25
    elif macd_signal == MacdSignal.NEUTRAL:
        score += 0.125

    # SMA 50 component (20%)
    if price_vs_sma50 == TrendDirection.ABOVE:
        score += 0.20

    # SMA 200 component (20%)
    if price_vs_sma200 == TrendDirection.ABOVE:
        score += 0.20

    # Volume component (10%)
    if volume_trend == VolumeTrend.HIGH:
        score += 0.10
    elif volume_trend == VolumeTrend.NEUTRAL:
        score += 0.05

    return round(score, 4)


def calculate_technicals(ticker: str) -> TechnicalAnalysis:
    """Orchestrator: fetch price history and compute all technical indicators."""
    history = get_price_history(ticker)
    closes = history["Close"]
    volumes = history["Volume"]

    rsi = calculate_rsi(closes)
    sma_50 = calculate_sma(closes, 50)
    sma_200 = calculate_sma(closes, 200)

    current_price = float(closes.iloc[-1])
    price_vs_sma50 = None
    if sma_50 is not None:
        price_vs_sma50 = (
            TrendDirection.ABOVE if current_price > sma_50 else TrendDirection.BELOW
        )

    price_vs_sma200 = None
    if sma_200 is not None:
        price_vs_sma200 = (
            TrendDirection.ABOVE if current_price > sma_200 else TrendDirection.BELOW
        )

    macd_line, signal_line, _ = calculate_macd(closes)
    macd_signal = interpret_macd(macd_line, signal_line)
    volume_trend = assess_volume_trend(volumes)

    technical_score = calculate_technical_score(
        rsi, macd_signal, price_vs_sma50, price_vs_sma200, volume_trend
    )

    return TechnicalAnalysis(
        rsi=rsi,
        rsi_interpretation=interpret_rsi(rsi) if rsi is not None else None,
        sma_50=sma_50,
        sma_200=sma_200,
        price_vs_sma50=price_vs_sma50,
        price_vs_sma200=price_vs_sma200,
        macd_signal=macd_signal,
        volume_trend=volume_trend,
        technical_score=technical_score,
    )
