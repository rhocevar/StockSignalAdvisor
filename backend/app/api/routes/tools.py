import logging

from fastapi import APIRouter, HTTPException

from app.agents.tools.fundamentals import calculate_fundamentals
from app.agents.tools.news_fetcher import fetch_news_headlines
from app.agents.tools.stock_data import get_company_name, get_stock_price
from app.agents.tools.technical import calculate_technicals
from app.models.domain import (
    FundamentalAnalysis,
    NewsSource,
    PriceData,
    TechnicalAnalysis,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tools")


@router.get("/stock-price/{ticker}", response_model=PriceData)
async def tool_stock_price(ticker: str) -> PriceData:
    """Fetch current price data for a ticker."""
    try:
        return get_stock_price(ticker.upper())
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("Failed to fetch stock price for %s", ticker)
        raise HTTPException(status_code=502, detail=f"Upstream API error: {e}")


@router.get("/company-name/{ticker}")
async def tool_company_name(ticker: str) -> dict:
    """Fetch the company name for a ticker."""
    try:
        name = get_company_name(ticker.upper())
        return {"ticker": ticker.upper(), "company_name": name}
    except Exception as e:
        logger.exception("Failed to fetch company name for %s", ticker)
        raise HTTPException(status_code=502, detail=f"Upstream API error: {e}")


@router.get("/technicals/{ticker}", response_model=TechnicalAnalysis)
async def tool_technicals(ticker: str) -> TechnicalAnalysis:
    """Calculate technical indicators for a ticker."""
    try:
        return calculate_technicals(ticker.upper())
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("Failed to calculate technicals for %s", ticker)
        raise HTTPException(status_code=502, detail=f"Upstream API error: {e}")


@router.get("/fundamentals/{ticker}", response_model=FundamentalAnalysis)
async def tool_fundamentals(ticker: str) -> FundamentalAnalysis:
    """Calculate fundamental analysis for a ticker."""
    try:
        return calculate_fundamentals(ticker.upper())
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("Failed to calculate fundamentals for %s", ticker)
        raise HTTPException(status_code=502, detail=f"Upstream API error: {e}")


@router.get("/news/{ticker}", response_model=list[NewsSource])
async def tool_news(ticker: str) -> list[NewsSource]:
    """Fetch recent news headlines for a ticker."""
    try:
        return fetch_news_headlines(ticker.upper())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Failed to fetch news for %s", ticker)
        raise HTTPException(status_code=502, detail=f"Upstream API error: {e}")
