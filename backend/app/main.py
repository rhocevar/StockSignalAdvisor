import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.config import settings

logging.basicConfig(level=settings.LOG_LEVEL)

app = FastAPI(
    title="Stock Signal Advisor",
    version="1.0.0",
    description="AI-powered stock analysis providing Buy/Hold/Sell recommendations",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")
