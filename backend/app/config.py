from typing import Optional

from pydantic_settings import BaseSettings

from app.enums import LLMProviderType, VectorStoreProviderType


class Settings(BaseSettings):
    # LLM Provider
    LLM_PROVIDER: LLMProviderType = LLMProviderType.OPENAI
    LLM_MODEL: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None

    # Vector Store
    VECTORSTORE_PROVIDER: VectorStoreProviderType = VectorStoreProviderType.PINECONE
    PINECONE_API_KEY: Optional[str] = None
    PINECONE_INDEX_NAME: str = "stock-signal-advisor"

    # Data Sources
    NEWS_API_KEY: Optional[str] = None

    # App Configuration
    CACHE_TTL_SECONDS: int = 3600
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
