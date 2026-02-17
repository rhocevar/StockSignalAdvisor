from pydantic_settings import BaseSettings

from app.enums import LLMProviderType, VectorStoreProviderType


class Settings(BaseSettings):
    # LLM Provider
    LLM_PROVIDER: LLMProviderType = LLMProviderType.OPENAI
    LLM_MODEL: str | None = None
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None

    # Vector Store
    VECTORSTORE_PROVIDER: VectorStoreProviderType = VectorStoreProviderType.PINECONE
    PINECONE_API_KEY: str | None = None
    PINECONE_INDEX_NAME: str = "stock-signal-advisor"

    # Data Sources
    NEWS_API_KEY: str | None = None

    # App Configuration
    CACHE_TTL_SECONDS: int = 3600
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
    ]

    model_config = {"env_file": (".env", "../.env"), "extra": "ignore"}


settings = Settings()
