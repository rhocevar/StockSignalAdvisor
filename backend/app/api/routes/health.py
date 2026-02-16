from datetime import datetime, timezone

from fastapi import APIRouter

from app.config import settings
from app.models.response import HealthResponse, ProviderStatus

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(
        providers=ProviderStatus(
            llm=settings.LLM_PROVIDER.value,
            vectorstore=settings.VECTORSTORE_PROVIDER.value,
        ),
        timestamp=datetime.now(timezone.utc),
    )
