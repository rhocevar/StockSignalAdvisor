import logging

from fastapi import APIRouter, HTTPException, Request

from app.agents.orchestrator import StockAnalysisOrchestrator
from app.models.request import AnalyzeRequest
from app.models.response import AnalyzeResponse
from app.providers.llm.base import LLMRateLimitError
from app.services.cache import get_cached
from app.services.limiter import check_uncached_rate_limit, refund_uncached_rate_limit

logger = logging.getLogger(__name__)

router = APIRouter()

_orchestrator = StockAnalysisOrchestrator()


@router.post("/signal", response_model=AnalyzeResponse)
async def analyze_stock(request: Request, body: AnalyzeRequest) -> AnalyzeResponse:
    # Short-circuit for cached tickers: cheap memory lookup, no LLM involved.
    cached = get_cached(body.ticker.upper())
    if cached is not None:
        result = cached.model_copy(deep=True)
        result.metadata.cached = True
        return result

    # Only uncached requests consume the rate limit (they will hit the LLM).
    check_uncached_rate_limit(request)
    try:
        return await _orchestrator.analyze(body)
    except ValueError as e:
        # Ticker not found — the LLM was never called, so refund the rate-limit
        # slot to avoid punishing users for typos.
        refund_uncached_rate_limit(request)
        raise HTTPException(status_code=404, detail=str(e))
    except LLMRateLimitError:
        raise HTTPException(
            status_code=429,
            detail="LLM provider rate limit exceeded. Please try again later.",
        )
    except Exception:
        logger.exception("Unexpected error analyzing %s", body.ticker)
        raise HTTPException(
            status_code=502,
            detail="Analysis service temporarily unavailable. Please try again.",
        )
