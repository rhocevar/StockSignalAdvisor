from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.enums import SignalType
from app.models.domain import (
    AnalysisMetadata,
    AnalysisResult,
    NewsSource,
    PriceData,
)

class AnalyzeResponse(BaseModel):
    ticker: str
    company_name: Optional[str] = None
    signal: SignalType
    confidence: float
    explanation: str
    analysis: AnalysisResult
    price_data: Optional[PriceData] = None
    sources: list[NewsSource] = []
    metadata: AnalysisMetadata


class ProviderStatus(BaseModel):
    llm: str
    vectorstore: str


class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "1.0.0"
    providers: ProviderStatus
    timestamp: datetime
