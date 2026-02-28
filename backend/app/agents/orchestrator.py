"""StockAnalysisOrchestrator — coordinates all tools and assembles AnalyzeResponse."""

import asyncio
import logging
from datetime import datetime, timezone

import yfinance as yf

from app.agents.agent import run_agent
from app.agents.tools.fundamentals import calculate_fundamentals
from app.agents.tools.news_fetcher import fetch_news_headlines
from app.agents.tools.sentiment import analyze_sentiment
from app.agents.tools.stock_data import get_company_name, get_stock_price, get_ticker
from app.agents.tools.technical import calculate_technicals
from app.config import settings
from app.models.domain import (
    AgentResult,
    AnalysisMetadata,
    AnalysisResult,
    FundamentalAnalysis,
    NewsSource,
    PriceData,
    SentimentAnalysis,
    TechnicalAnalysis,
)
from app.models.request import AnalyzeRequest
from app.models.response import AnalyzeResponse
from app.providers.llm.base import LLMRateLimitError
from app.services.cache import get_cached, set_cached

logger = logging.getLogger(__name__)

# Dynamic pillar weights for confidence calculation
_WEIGHTS_ALL = {"technical": 0.40, "fundamental": 0.40, "sentiment": 0.20}
_WEIGHTS_NO_FUNDAMENTAL = {"technical": 0.70, "sentiment": 0.30}
_WEIGHTS_NO_SENTIMENT = {"technical": 0.60, "fundamental": 0.40}
_WEIGHTS_TECHNICAL_ONLY = {"technical": 1.00}


def _compute_weighted_confidence(
    technical: TechnicalAnalysis | None,
    fundamentals: FundamentalAnalysis | None,
    sentiment: SentimentAnalysis | None,
) -> float:
    """Compute a weighted confidence score from available pillar scores."""
    tech_score = technical.technical_score if technical and technical.technical_score is not None else None
    fund_score = fundamentals.fundamental_score if fundamentals and fundamentals.fundamental_score is not None else None
    sent_score = sentiment.score if sentiment and sentiment.score is not None else None

    has_tech = tech_score is not None
    has_fund = fund_score is not None
    has_sent = sent_score is not None

    if has_tech and has_fund and has_sent:
        weights = _WEIGHTS_ALL
    elif has_tech and has_fund:
        weights = _WEIGHTS_NO_SENTIMENT
    elif has_tech and has_sent:
        weights = _WEIGHTS_NO_FUNDAMENTAL
    elif has_tech:
        weights = _WEIGHTS_TECHNICAL_ONLY
    else:
        return 0.5  # Neutral fallback

    score = 0.0
    if "technical" in weights and tech_score is not None:
        score += weights["technical"] * tech_score
    if "fundamental" in weights and fund_score is not None:
        score += weights["fundamental"] * fund_score
    if "sentiment" in weights and sent_score is not None:
        score += weights["sentiment"] * sent_score

    return round(max(0.0, min(1.0, score)), 4)


class StockAnalysisOrchestrator:
    """Coordinates all analysis tools and assembles the full AnalyzeResponse."""

    async def analyze(self, request: AnalyzeRequest) -> AnalyzeResponse:
        ticker = request.ticker.upper()

        # 1. Cache check
        cached = get_cached(ticker)
        if cached is not None:
            result = cached.model_copy(deep=True)
            result.metadata.cached = True
            return result

        # 2. Create shared yf.Ticker and pre-fetch .info (lazy property).
        #    This avoids a race condition where concurrent threads all trigger
        #    the first .info fetch simultaneously, causing some to get None.
        stock = await asyncio.to_thread(get_ticker, ticker)
        await asyncio.to_thread(lambda: stock.info)

        # 3. Parallel data gathering
        tasks: dict[str, asyncio.Task] = {}

        tasks["price"] = asyncio.create_task(
            asyncio.to_thread(get_stock_price, stock)
        )
        tasks["company_name"] = asyncio.create_task(
            asyncio.to_thread(get_company_name, stock)
        )

        if request.include_technicals:
            tasks["technicals"] = asyncio.create_task(
                asyncio.to_thread(calculate_technicals, stock)
            )

        if request.include_fundamentals:
            tasks["fundamentals"] = asyncio.create_task(
                asyncio.to_thread(calculate_fundamentals, stock)
            )

        if request.include_news:
            tasks["news"] = asyncio.create_task(
                asyncio.to_thread(fetch_news_headlines, ticker)
            )

        # Await all tasks, catching errors gracefully
        results: dict[str, object] = {}
        for key, task in tasks.items():
            try:
                results[key] = await task
            except ValueError as e:
                # Expected domain errors (e.g. ticker not found) — no traceback
                logger.warning("Failed to gather %s for %s: %s", key, ticker, e)
                results[key] = None
            except Exception:
                logger.exception("Failed to gather %s for %s", key, ticker)
                results[key] = None

        price_data: PriceData | None = results.get("price")
        company_name: str | None = results.get("company_name")
        technicals: TechnicalAnalysis | None = results.get("technicals")
        fundamentals: FundamentalAnalysis | None = results.get("fundamentals")
        headlines: list[NewsSource] | None = results.get("news")

        if price_data is None:
            raise ValueError(
                f"Ticker '{ticker}' not found. Verify the symbol and try again."
            )

        # 4. Sentiment (requires news headlines)
        sentiment: SentimentAnalysis | None = None
        if headlines:
            try:
                sentiment, headlines = await analyze_sentiment(headlines)
            except Exception:
                logger.exception("Failed to analyze sentiment for %s", ticker)

        # 5. Agent — signal + explanation
        try:
            agent_result = await run_agent(ticker)
        except LLMRateLimitError:
            raise  # propagate → analysis.py → 429
        except Exception:
            logger.exception("Agent failed for %s, using fallback HOLD signal", ticker)
            agent_result = AgentResult(
                explanation="Signal analysis temporarily unavailable. Technical and fundamental data are shown below."
            )

        # 6. Compute weighted confidence from pillar scores
        confidence = _compute_weighted_confidence(technicals, fundamentals, sentiment)

        # 7. Assemble response
        response = AnalyzeResponse(
            ticker=ticker,
            company_name=company_name,
            signal=agent_result.signal,
            confidence=confidence,
            explanation=agent_result.explanation,
            analysis=AnalysisResult(
                technical=technicals,
                fundamentals=fundamentals,
                sentiment=sentiment,
            ),
            price_data=price_data,
            sources=headlines or [],
            metadata=AnalysisMetadata(
                generated_at=datetime.now(timezone.utc),
                llm_provider=settings.LLM_PROVIDER.value,
                model_used=settings.LLM_MODEL or "not configured",
                vectorstore_provider=settings.VECTORSTORE_PROVIDER.value,
                cached=False,
            ),
        )

        # 8. Cache store
        set_cached(ticker, response)

        return response
