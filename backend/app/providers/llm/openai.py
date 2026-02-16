from openai import AsyncOpenAI

from app.enums import OpenAIModel, OpenAIEmbeddingModel
from .base import LLMProvider, ChatMessage, LLMResponse


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = OpenAIModel.GPT_4O_MINI):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.embedding_model = OpenAIEmbeddingModel.TEXT_EMBEDDING_3_SMALL

    async def complete(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.3,
        max_tokens: int = 1000,
        json_mode: bool = False,
    ) -> LLMResponse:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": m.role.value, "content": m.content} for m in messages],
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"} if json_mode else None,
        )
        return LLMResponse(
            content=response.choices[0].message.content,
            model=self.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
            },
        )

    async def embed(self, text: str) -> list[float]:
        response = await self.client.embeddings.create(
            model=self.embedding_model,
            input=text,
        )
        return response.data[0].embedding

    def get_model_name(self) -> str:
        return self.model
