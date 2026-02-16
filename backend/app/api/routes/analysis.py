from datetime import datetime, timezone

from fastapi import APIRouter

from app.config import settings
from app.enums import SignalType
from app.models.domain import AnalysisMetadata, AnalysisResult
from app.models.request import AnalyzeRequest
from app.models.response import AnalyzeResponse

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_stock(request: AnalyzeRequest) -> AnalyzeResponse:
    # Stub implementation — will be replaced by orchestrator in Day 12
    ticker = request.ticker.upper()

    return AnalyzeResponse(
        ticker=ticker,
        company_name=f"{ticker} Inc.",
        signal=SignalType.HOLD,
        confidence=0.5,
        explanation=(
            f"Stub analysis for {ticker}. "
            "The full AI-powered analysis pipeline is not yet connected."
        ),
        analysis=AnalysisResult(),
        metadata=AnalysisMetadata(
            generated_at=datetime.now(timezone.utc),
            llm_provider=settings.LLM_PROVIDER.value,
            model_used=settings.LLM_MODEL or "not configured",
            vectorstore_provider=settings.VECTORSTORE_PROVIDER.value,
            cached=False,
        ),
    )
