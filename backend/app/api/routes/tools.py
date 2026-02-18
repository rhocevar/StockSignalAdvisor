import logging

from fastapi import APIRouter, HTTPException, Path, Query

from app.agents.tools.fundamentals import calculate_fundamentals
from app.agents.tools.news_fetcher import fetch_news_headlines
from app.agents.tools.sentiment import analyze_sentiment
from app.agents.tools.stock_data import get_company_name, get_stock_price, get_ticker
from app.agents.tools.technical import calculate_technicals
from app.providers.llm.base import LLMRateLimitError
from app.providers.vectorstore.base import SearchResult
from app.rag.retriever import retrieve
from app.models.domain import (
    FundamentalAnalysis,
    NewsSource,
    PriceData,
    SentimentAnalysis,
    TechnicalAnalysis,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tools")

_TICKER_PATTERN = r"^[A-Za-z0-9.\-]{1,10}$"

TickerPath = Path(..., pattern=_TICKER_PATTERN, description="Stock ticker symbol")


@router.get("/stock-price/{ticker}", response_model=PriceData)
def tool_stock_price(ticker: str = TickerPath) -> PriceData:
    """Fetch current price data for a ticker."""
    try:
        stock = get_ticker(ticker.upper())
        return get_stock_price(stock)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("Failed to fetch stock price for %s", ticker)
        raise HTTPException(status_code=502, detail="Upstream data provider error")


@router.get("/company-name/{ticker}")
def tool_company_name(ticker: str = TickerPath) -> dict:
    """Fetch the company name for a ticker."""
    try:
        stock = get_ticker(ticker.upper())
        name = get_company_name(stock)
        return {"ticker": ticker.upper(), "company_name": name}
    except Exception:
        logger.exception("Failed to fetch company name for %s", ticker)
        raise HTTPException(status_code=502, detail="Upstream data provider error")


@router.get("/technicals/{ticker}", response_model=TechnicalAnalysis)
def tool_technicals(ticker: str = TickerPath) -> TechnicalAnalysis:
    """Calculate technical indicators for a ticker."""
    try:
        stock = get_ticker(ticker.upper())
        return calculate_technicals(stock)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("Failed to calculate technicals for %s", ticker)
        raise HTTPException(status_code=502, detail="Upstream data provider error")


@router.get("/fundamentals/{ticker}", response_model=FundamentalAnalysis)
def tool_fundamentals(ticker: str = TickerPath) -> FundamentalAnalysis:
    """Calculate fundamental analysis for a ticker."""
    try:
        stock = get_ticker(ticker.upper())
        return calculate_fundamentals(stock)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("Failed to calculate fundamentals for %s", ticker)
        raise HTTPException(status_code=502, detail="Upstream data provider error")


@router.get("/news/{ticker}", response_model=list[NewsSource])
def tool_news(ticker: str = TickerPath) -> list[NewsSource]:
    """Fetch recent news headlines for a ticker."""
    try:
        return fetch_news_headlines(ticker.upper())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Failed to fetch news for %s", ticker)
        raise HTTPException(status_code=502, detail="Upstream data provider error")


@router.get("/sentiment/{ticker}", response_model=SentimentAnalysis)
async def tool_sentiment(ticker: str = TickerPath) -> SentimentAnalysis:
    """Fetch news and analyze sentiment via LLM for a ticker."""
    try:
        headlines = fetch_news_headlines(ticker.upper())
        return await analyze_sentiment(headlines)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except LLMRateLimitError:
        raise HTTPException(
            status_code=429,
            detail="LLM provider rate limit exceeded. Please try again later.",
        )
    except Exception as e:
        logger.exception("Failed to analyze sentiment for %s", ticker)
        raise HTTPException(status_code=502, detail="Upstream data provider error")


@router.get("/rag-search", response_model=list[SearchResult])
async def tool_rag_search(
    query: str = Query(..., min_length=1, description="Natural language search query"),
    top_k: int = Query(5, ge=1, le=20, description="Max results to return"),
) -> list[SearchResult]:
    """Search the RAG vector store for relevant financial context."""
    try:
        return await retrieve(query, top_k=top_k)
    except LLMRateLimitError:
        raise HTTPException(
            status_code=429,
            detail="LLM provider rate limit exceeded. Please try again later.",
        )
    except Exception:
        logger.exception("RAG search failed for query: %s", query)
        raise HTTPException(status_code=502, detail="Upstream data provider error")
