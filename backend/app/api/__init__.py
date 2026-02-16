from fastapi import APIRouter

from .routes import analysis_router, health_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(analysis_router, tags=["analysis"])
