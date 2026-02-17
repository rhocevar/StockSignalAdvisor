from abc import ABC, abstractmethod
from pydantic import BaseModel

from app.enums import ChatMessageRole


class LLMRateLimitError(Exception):
    """Raised when the LLM provider returns a rate-limit or quota error."""


class ChatMessage(BaseModel):
    role: ChatMessageRole
    content: str


class LLMResponse(BaseModel):
    content: str
    model: str
    usage: dict  # token counts


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def complete(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.3,
        max_tokens: int = 1000,
        json_mode: bool = False,
    ) -> LLMResponse:
        """Generate a completion from the LLM."""
        pass

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Generate embeddings for text."""
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Return the model identifier."""
        pass
