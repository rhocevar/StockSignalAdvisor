import logging

from fastapi import APIRouter, HTTPException, Request

from app.agents.orchestrator import StockAnalysisOrchestrator
from app.models.request import AnalyzeRequest
from app.models.response import AnalyzeResponse
from app.providers.llm.base import LLMRateLimitError
from app.services.cache import get_cached
from app.services.limiter import check_uncached_rate_limit

logger = logging.getLogger(__name__)

router = APIRouter()

_orchestrator = StockAnalysisOrchestrator()


@router.post("/signal", response_model=AnalyzeResponse)
async def analyze_stock(request: Request, body: AnalyzeRequest) -> AnalyzeResponse:
    # Only count requests toward the rate limit when they will hit the LLM.
    # Cached responses are cheap memory lookups and need no throttling.
    if not get_cached(body.ticker):
        check_uncached_rate_limit(request)
    try:
        return await _orchestrator.analyze(body)
    except ValueError as e:
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
