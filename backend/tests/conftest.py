from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.enums import (
    ChatMessageRole,
    DocumentType,
    OpenAIModel,
    OpenAIEmbeddingModel,
    AnthropicModel,
)
from app.providers.llm.base import ChatMessage


@pytest.fixture
def sample_messages():
    return [
        ChatMessage(role=ChatMessageRole.SYSTEM, content="You are a helpful assistant."),
        ChatMessage(role=ChatMessageRole.USER, content="Say hello"),
    ]


@pytest.fixture
def sample_user_message():
    return [ChatMessage(role=ChatMessageRole.USER, content="Say hello")]


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI chat completion response."""
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message.content = "Hello! How can I help?"
    response.usage.prompt_tokens = 10
    response.usage.completion_tokens = 5
    return response


@pytest.fixture
def mock_openai_embedding_response():
    """Mock OpenAI embedding response."""
    response = MagicMock()
    response.data = [MagicMock()]
    response.data[0].embedding = [0.1] * 1536
    return response


@pytest.fixture
def mock_anthropic_response():
    """Mock Anthropic message response."""
    response = MagicMock()
    response.content = [MagicMock()]
    response.content[0].text = "Hello from Claude!"
    response.usage.input_tokens = 10
    response.usage.output_tokens = 5
    return response


@pytest.fixture
def openai_provider(mock_openai_response, mock_openai_embedding_response):
    """OpenAIProvider with mocked client."""
    with patch("app.providers.llm.openai.AsyncOpenAI") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_openai_response)
        mock_client.embeddings.create = AsyncMock(return_value=mock_openai_embedding_response)
        mock_client_cls.return_value = mock_client

        from app.providers.llm.openai import OpenAIProvider

        provider = OpenAIProvider(api_key="test-key")
        yield provider


@pytest.fixture
def anthropic_provider(mock_anthropic_response):
    """AnthropicProvider with mocked client."""
    with patch("app.providers.llm.anthropic.AsyncAnthropic") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_anthropic_response)
        mock_client_cls.return_value = mock_client

        from app.providers.llm.anthropic import AnthropicProvider

        provider = AnthropicProvider(api_key="test-key")
        yield provider


@pytest.fixture
def pinecone_provider():
    """PineconeProvider with mocked client."""
    with patch("app.providers.vectorstore.pinecone.Pinecone") as mock_pc_cls:
        mock_pc = MagicMock()
        mock_index = MagicMock()
        mock_pc.Index.return_value = mock_index
        mock_pc_cls.return_value = mock_pc

        from app.providers.vectorstore.pinecone import PineconeProvider

        provider = PineconeProvider(api_key="test-key", index_name="test-index")
        yield provider
