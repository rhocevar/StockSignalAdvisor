from anthropic import AsyncAnthropic, RateLimitError

from app.enums import AnthropicModel, ChatMessageRole
from .base import LLMProvider, LLMRateLimitError, ChatMessage, LLMResponse


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = AnthropicModel.CLAUDE_3_5_HAIKU):
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model

    async def complete(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.3,
        max_tokens: int = 1000,
        json_mode: bool = False,
    ) -> LLMResponse:
        system = None
        chat_messages = []
        for m in messages:
            if m.role == ChatMessageRole.SYSTEM:
                system = m.content
            else:
                chat_messages.append({"role": m.role.value, "content": m.content})

        if json_mode:
            system = (system or "") + "\n\nRespond with valid JSON only."

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system,
                messages=chat_messages,
            )
        except RateLimitError as e:
            raise LLMRateLimitError(str(e)) from e
        return LLMResponse(
            content=response.content[0].text,
            model=self.model,
            usage={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
            },
        )

    async def embed(self, text: str) -> list[float]:
        raise NotImplementedError(
            "Anthropic doesn't provide embeddings. "
            "Configure EMBEDDING_PROVIDER=openai separately."
        )

    def get_model_name(self) -> str:
        return self.model
