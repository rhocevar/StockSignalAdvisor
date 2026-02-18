from fastapi import APIRouter

from app.agents.orchestrator import StockAnalysisOrchestrator
from app.models.request import AnalyzeRequest
from app.models.response import AnalyzeResponse

router = APIRouter()

_orchestrator = StockAnalysisOrchestrator()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_stock(request: AnalyzeRequest) -> AnalyzeResponse:
    return await _orchestrator.analyze(request)
