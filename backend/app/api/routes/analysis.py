import logging

from fastapi import APIRouter, HTTPException

from app.agents.orchestrator import StockAnalysisOrchestrator
from app.models.request import AnalyzeRequest
from app.models.response import AnalyzeResponse
from app.providers.llm.base import LLMRateLimitError

logger = logging.getLogger(__name__)

router = APIRouter()

_orchestrator = StockAnalysisOrchestrator()


@router.post("/signal", response_model=AnalyzeResponse)
async def analyze_stock(request: AnalyzeRequest) -> AnalyzeResponse:
    try:
        return await _orchestrator.analyze(request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except LLMRateLimitError:
        raise HTTPException(
            status_code=429,
            detail="LLM provider rate limit exceeded. Please try again later.",
        )
    except Exception:
        logger.exception("Unexpected error analyzing %s", request.ticker)
        raise HTTPException(
            status_code=502,
            detail="Analysis service temporarily unavailable. Please try again.",
        )
