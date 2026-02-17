from app.config import settings
from app.enums import LLMProviderType, OpenAIModel, AnthropicModel
from .base import LLMProvider
from .openai import OpenAIProvider
from .anthropic import AnthropicProvider


def get_llm_provider() -> LLMProvider:
    """Factory function to get the configured LLM provider."""

    if settings.LLM_PROVIDER == LLMProviderType.OPENAI:
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        return OpenAIProvider(
            api_key=settings.OPENAI_API_KEY,
            model=settings.LLM_MODEL or OpenAIModel.GPT_4O_MINI,
        )
    elif settings.LLM_PROVIDER == LLMProviderType.ANTHROPIC:
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic")
        return AnthropicProvider(
            api_key=settings.ANTHROPIC_API_KEY,
            model=settings.LLM_MODEL or AnthropicModel.CLAUDE_3_5_HAIKU,
        )
    else:
        raise ValueError(f"Unknown LLM provider: {settings.LLM_PROVIDER}")
