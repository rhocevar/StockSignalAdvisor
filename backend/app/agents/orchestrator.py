"""StockAnalysisOrchestrator — coordinates all tools and assembles AnalyzeResponse."""

import asyncio
import logging
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable

import yfinance as yf

from app.agents.agent import run_agent
from app.agents.tools.fundamentals import calculate_fundamentals
from app.agents.tools.news_fetcher import fetch_news_headlines
from app.agents.tools.sentiment import analyze_sentiment
from app.agents.tools.stock_data import get_company_name, get_stock_price, get_ticker, is_equity
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


# ---------------------------------------------------------------------------
# Streaming types
# ---------------------------------------------------------------------------


@dataclass
class PillarResult:
    """Pairs a pillar label with its computed data (or None on failure)."""

    pillar: str
    data: TechnicalAnalysis | FundamentalAnalysis | None


@dataclass
class StreamEvent:
    """A single SSE event produced by analyze_streaming()."""

    type: str  # "technical" | "fundamental" | "sentiment" | "complete" | "error"
    data: dict[str, Any]


async def _pillar(label: str, fn: Callable, *args: Any) -> PillarResult:
    """Run a synchronous pillar tool in a thread pool; swallow errors gracefully."""
    try:
        data = await asyncio.to_thread(fn, *args)
    except Exception:
        logger.exception("Failed to calculate %s pillar", label)
        data = None
    return PillarResult(pillar=label, data=data)


# ---------------------------------------------------------------------------
# Confidence calculation
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


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
        # company_name is a pure dict lookup on pre-fetched stock.info — no I/O needed.
        # Resolve it synchronously so it can be passed to the news query for disambiguation
        # (e.g. ticker "PBR" → query '"Petrobras"' instead of just "PBR").
        company_name: str | None = get_company_name(stock)
        # ETFs, mutual funds, and indices lack company-level fundamentals —
        # skip the fundamental pillar to avoid a misleadingly low score.
        include_fundamentals = request.include_fundamentals and is_equity(stock)

        tasks: dict[str, asyncio.Task] = {}

        tasks["price"] = asyncio.create_task(
            asyncio.to_thread(get_stock_price, stock)
        )

        if request.include_technicals:
            tasks["technicals"] = asyncio.create_task(
                asyncio.to_thread(calculate_technicals, stock)
            )

        if include_fundamentals:
            tasks["fundamentals"] = asyncio.create_task(
                asyncio.to_thread(calculate_fundamentals, stock)
            )

        if request.include_news:
            tasks["news"] = asyncio.create_task(
                asyncio.to_thread(fetch_news_headlines, ticker, company_name)
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
                sentiment, headlines = await analyze_sentiment(
                    headlines, ticker=ticker, company_name=company_name
                )
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

    async def analyze_streaming(self, ticker: str) -> AsyncGenerator[StreamEvent, None]:
        """Stream pillar results as SSE events as each completes.

        Always runs the full analysis (all three pillars). Emits:
        - ``technical`` and ``fundamental`` events in completion order
        - ``sentiment`` event after news fetch + LLM classification
        - ``complete`` event with the full AnalyzeResponse payload
        - ``error`` event (code 404 or 429) on unrecoverable failures

        For cached tickers a single ``complete`` event is emitted immediately.
        """
        ticker = ticker.upper()

        # 1. Cache check — emit single complete event and close
        cached = get_cached(ticker)
        if cached is not None:
            result = cached.model_copy(deep=True)
            result.metadata.cached = True
            yield StreamEvent(type="complete", data=result.model_dump(mode="json"))
            return

        # 2. Shared yf.Ticker setup (same race-condition guard as analyze())
        stock = await asyncio.to_thread(get_ticker, ticker)
        await asyncio.to_thread(lambda: stock.info)
        company_name: str | None = get_company_name(stock)
        # ETFs, mutual funds, and indices lack company-level fundamentals —
        # skip the fundamental pillar to avoid a misleadingly low score.
        run_fundamentals = is_equity(stock)

        # 3. Start all tasks in parallel before processing any results
        price_task = asyncio.create_task(asyncio.to_thread(get_stock_price, stock))
        news_task = asyncio.create_task(
            asyncio.to_thread(fetch_news_headlines, ticker, company_name)
        )
        tech_task = asyncio.create_task(_pillar("technical", calculate_technicals, stock))
        fund_task = asyncio.create_task(_pillar("fundamental", calculate_fundamentals, stock)) if run_fundamentals else None

        # 4. Emit technical / fundamental as each completes (order is non-deterministic)
        pillar_results: dict[str, TechnicalAnalysis | FundamentalAnalysis | None] = {}
        active_pillar_tasks = [t for t in [tech_task, fund_task] if t is not None]
        for fut in asyncio.as_completed(active_pillar_tasks):
            result: PillarResult = await fut  # _pillar() swallows exceptions internally
            pillar_results[result.pillar] = result.data
            if result.data is not None:
                yield StreamEvent(type=result.pillar, data=result.data.model_dump(mode="json"))

        # 5. Sentiment (depends on news headlines)
        headlines: list[NewsSource] | None = None
        try:
            headlines = await news_task
        except Exception:
            logger.exception("Failed to fetch news for %s", ticker)

        sentiment: SentimentAnalysis | None = None
        if headlines:
            try:
                sentiment, headlines = await analyze_sentiment(
                    headlines, ticker=ticker, company_name=company_name
                )
                yield StreamEvent(
                    type="sentiment",
                    data={
                        "analysis": sentiment.model_dump(mode="json"),
                        "sources": [s.model_dump(mode="json") for s in headlines],
                    },
                )
            except Exception:
                logger.exception("Failed to analyze sentiment for %s", ticker)

        # 6. Price data (running in parallel since step 3; likely done by now)
        price_data: PriceData | None = None
        try:
            price_data = await price_task
        except Exception:
            logger.exception("Failed to get price data for %s", ticker)

        if price_data is None:
            yield StreamEvent(
                type="error",
                data={
                    "code": 404,
                    "message": f"Ticker '{ticker}' not found or has no market data.",
                },
            )
            return

        # 7. Agent — signal + explanation
        try:
            agent_result = await run_agent(ticker)
        except LLMRateLimitError:
            yield StreamEvent(
                type="error",
                data={"code": 429, "message": "LLM rate limit exceeded. Please try again later."},
            )
            return
        except Exception:
            logger.exception("Agent failed for %s, using fallback HOLD signal", ticker)
            agent_result = AgentResult(
                explanation="Signal analysis temporarily unavailable. Technical and fundamental data are shown below."
            )

        # 8. Confidence + assemble full response
        technicals: TechnicalAnalysis | None = pillar_results.get("technical")
        fundamentals: FundamentalAnalysis | None = pillar_results.get("fundamental")
        confidence = _compute_weighted_confidence(technicals, fundamentals, sentiment)

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

        set_cached(ticker, response)
        yield StreamEvent(type="complete", data=response.model_dump(mode="json"))
