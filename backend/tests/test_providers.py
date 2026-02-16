from unittest.mock import patch, MagicMock

import pytest
from pydantic import ValidationError

from app.enums import (
    ChatMessageRole,
    DocumentType,
    LLMProviderType,
    VectorStoreProviderType,
    OpenAIModel,
    AnthropicModel,
)
from app.providers.llm.base import LLMProvider, ChatMessage, LLMResponse
from app.providers.llm.openai import OpenAIProvider
from app.providers.llm.anthropic import AnthropicProvider
from app.providers.vectorstore.base import VectorStoreProvider, Document, SearchResult
from app.providers.vectorstore.pinecone import (
    PineconeProvider,
    PineconeMetadataKey,
    PineconeVectorKey,
    PineconeResultKey,
)


# ─── Pydantic Model Tests ────────────────────────────────────────────


class TestChatMessage:
    def test_valid_roles(self):
        for role in ChatMessageRole:
            msg = ChatMessage(role=role, content="test")
            assert msg.role == role

    def test_invalid_role_rejected(self):
        with pytest.raises(ValidationError):
            ChatMessage(role="invalid_role", content="test")


class TestLLMResponse:
    def test_construction(self):
        resp = LLMResponse(
            content="hello",
            model="gpt-4o-mini",
            usage={"prompt_tokens": 10, "completion_tokens": 5},
        )
        assert resp.content == "hello"
        assert resp.model == "gpt-4o-mini"
        assert resp.usage["prompt_tokens"] == 10


class TestDocument:
    def test_requires_doc_type(self):
        with pytest.raises(ValidationError):
            Document(id="1", content="test")

    def test_valid_doc_types(self):
        for doc_type in DocumentType:
            doc = Document(id="1", content="test", doc_type=doc_type)
            assert doc.doc_type == doc_type

    def test_optional_fields(self):
        doc = Document(id="1", content="test", doc_type=DocumentType.NEWS)
        assert doc.embedding is None
        assert doc.metadata == {}

    def test_with_all_fields(self):
        doc = Document(
            id="1",
            content="test",
            doc_type=DocumentType.ANALYSIS,
            embedding=[0.1, 0.2],
            metadata={"ticker": "AAPL"},
        )
        assert doc.embedding == [0.1, 0.2]
        assert doc.metadata["ticker"] == "AAPL"


class TestSearchResult:
    def test_construction(self):
        result = SearchResult(id="1", content="test", score=0.95, metadata={})
        assert result.score == 0.95


# ─── Interface Compliance Tests ───────────────────────────────────────


class TestInterfaceCompliance:
    def test_llm_provider_is_abstract(self):
        with pytest.raises(TypeError, match="abstract"):
            LLMProvider()

    def test_vectorstore_provider_is_abstract(self):
        with pytest.raises(TypeError, match="abstract"):
            VectorStoreProvider()

    def test_openai_implements_llm_provider(self):
        assert issubclass(OpenAIProvider, LLMProvider)

    def test_anthropic_implements_llm_provider(self):
        assert issubclass(AnthropicProvider, LLMProvider)

    def test_pinecone_implements_vectorstore_provider(self):
        assert issubclass(PineconeProvider, VectorStoreProvider)


# ─── OpenAI Provider Tests ────────────────────────────────────────────


class TestOpenAIProvider:
    async def test_complete_returns_llm_response(self, openai_provider, sample_user_message):
        response = await openai_provider.complete(sample_user_message)
        assert isinstance(response, LLMResponse)
        assert response.content == "Hello! How can I help?"
        assert response.usage["prompt_tokens"] == 10
        assert response.usage["completion_tokens"] == 5

    async def test_complete_passes_correct_params(self, openai_provider, sample_user_message):
        await openai_provider.complete(
            sample_user_message, temperature=0.7, max_tokens=500
        )
        call_kwargs = openai_provider.client.chat.completions.create.call_args.kwargs
        assert call_kwargs["temperature"] == 0.7
        assert call_kwargs["max_tokens"] == 500
        assert call_kwargs["response_format"] is None

    async def test_complete_json_mode(self, openai_provider, sample_user_message):
        await openai_provider.complete(sample_user_message, json_mode=True)
        call_kwargs = openai_provider.client.chat.completions.create.call_args.kwargs
        assert call_kwargs["response_format"] == {"type": "json_object"}

    async def test_complete_serializes_role_as_value(self, openai_provider, sample_user_message):
        await openai_provider.complete(sample_user_message)
        call_kwargs = openai_provider.client.chat.completions.create.call_args.kwargs
        assert call_kwargs["messages"][0]["role"] == "user"

    async def test_embed_returns_float_list(self, openai_provider):
        embedding = await openai_provider.embed("test text")
        assert isinstance(embedding, list)
        assert len(embedding) == 1536
        assert all(isinstance(v, float) for v in embedding)

    def test_get_model_name(self, openai_provider):
        assert openai_provider.get_model_name() == OpenAIModel.GPT_4O_MINI


# ─── Anthropic Provider Tests ─────────────────────────────────────────


class TestAnthropicProvider:
    async def test_complete_returns_llm_response(self, anthropic_provider, sample_user_message):
        response = await anthropic_provider.complete(sample_user_message)
        assert isinstance(response, LLMResponse)
        assert response.content == "Hello from Claude!"
        assert response.usage["prompt_tokens"] == 10
        assert response.usage["completion_tokens"] == 5

    async def test_complete_extracts_system_message(self, anthropic_provider, sample_messages):
        await anthropic_provider.complete(sample_messages)
        call_kwargs = anthropic_provider.client.messages.create.call_args.kwargs
        assert call_kwargs["system"] == "You are a helpful assistant."
        assert len(call_kwargs["messages"]) == 1
        assert call_kwargs["messages"][0]["role"] == "user"

    async def test_complete_json_mode_appends_instruction(
        self, anthropic_provider, sample_messages
    ):
        await anthropic_provider.complete(sample_messages, json_mode=True)
        call_kwargs = anthropic_provider.client.messages.create.call_args.kwargs
        assert call_kwargs["system"].endswith("\n\nRespond with valid JSON only.")

    async def test_embed_raises_not_implemented(self, anthropic_provider):
        with pytest.raises(NotImplementedError, match="Anthropic doesn't provide embeddings"):
            await anthropic_provider.embed("test text")

    def test_get_model_name(self, anthropic_provider):
        assert anthropic_provider.get_model_name() == AnthropicModel.CLAUDE_3_5_HAIKU


# ─── Pinecone Provider Tests ─────────────────────────────────────────


class TestPineconeProvider:
    async def test_upsert_returns_count(self, pinecone_provider):
        docs = [
            Document(
                id="1",
                content="test",
                doc_type=DocumentType.NEWS,
                embedding=[0.1] * 1536,
            ),
            Document(
                id="2",
                content="test2",
                doc_type=DocumentType.ANALYSIS,
                embedding=[0.2] * 1536,
            ),
        ]
        count = await pinecone_provider.upsert(docs)
        assert count == 2
        pinecone_provider.index.upsert.assert_called_once()

    async def test_upsert_uses_enum_keys(self, pinecone_provider):
        doc = Document(
            id="1",
            content="test content",
            doc_type=DocumentType.NEWS,
            embedding=[0.1] * 3,
            metadata={"ticker": "AAPL"},
        )
        await pinecone_provider.upsert([doc])
        call_args = pinecone_provider.index.upsert.call_args.kwargs
        vector = call_args["vectors"][0]
        assert PineconeVectorKey.ID in vector
        assert PineconeVectorKey.VALUES in vector
        assert PineconeVectorKey.METADATA in vector
        metadata = vector[PineconeVectorKey.METADATA]
        assert metadata[PineconeMetadataKey.CONTENT] == "test content"
        assert metadata[PineconeMetadataKey.DOC_TYPE] == "news"
        assert metadata["ticker"] == "AAPL"

    async def test_search_returns_search_results(self, pinecone_provider):
        pinecone_provider.index.query.return_value = {
            PineconeResultKey.MATCHES: [
                {
                    PineconeResultKey.ID: "1",
                    PineconeResultKey.SCORE: 0.95,
                    PineconeResultKey.METADATA: {
                        PineconeMetadataKey.CONTENT: "matching content",
                    },
                }
            ]
        }
        results = await pinecone_provider.search([0.1] * 1536, top_k=1)
        assert len(results) == 1
        assert isinstance(results[0], SearchResult)
        assert results[0].id == "1"
        assert results[0].score == 0.95
        assert results[0].content == "matching content"

    async def test_search_empty_results(self, pinecone_provider):
        pinecone_provider.index.query.return_value = {PineconeResultKey.MATCHES: []}
        results = await pinecone_provider.search([0.1] * 1536)
        assert results == []

    async def test_delete_returns_count(self, pinecone_provider):
        count = await pinecone_provider.delete(["1", "2", "3"])
        assert count == 3
        pinecone_provider.index.delete.assert_called_once_with(ids=["1", "2", "3"])


# ─── Factory Tests ────────────────────────────────────────────────────


class TestLLMFactory:
    @patch("app.providers.llm.factory.settings")
    @patch("app.providers.llm.openai.AsyncOpenAI")
    def test_returns_openai_provider(self, mock_openai, mock_settings):
        mock_settings.LLM_PROVIDER = LLMProviderType.OPENAI
        mock_settings.OPENAI_API_KEY = "test-key"
        mock_settings.LLM_MODEL = None

        from app.providers.llm.factory import get_llm_provider

        provider = get_llm_provider()
        assert isinstance(provider, OpenAIProvider)

    @patch("app.providers.llm.factory.settings")
    @patch("app.providers.llm.anthropic.AsyncAnthropic")
    def test_returns_anthropic_provider(self, mock_anthropic, mock_settings):
        mock_settings.LLM_PROVIDER = LLMProviderType.ANTHROPIC
        mock_settings.ANTHROPIC_API_KEY = "test-key"
        mock_settings.LLM_MODEL = None

        from app.providers.llm.factory import get_llm_provider

        provider = get_llm_provider()
        assert isinstance(provider, AnthropicProvider)

    @patch("app.providers.llm.factory.settings")
    def test_raises_for_unknown_provider(self, mock_settings):
        mock_settings.LLM_PROVIDER = "unknown"

        from app.providers.llm.factory import get_llm_provider

        with pytest.raises(ValueError, match="Unknown LLM provider"):
            get_llm_provider()


class TestVectorStoreFactory:
    @patch("app.providers.vectorstore.factory.settings")
    @patch("app.providers.vectorstore.pinecone.Pinecone")
    def test_returns_pinecone_provider(self, mock_pc, mock_settings):
        mock_settings.VECTORSTORE_PROVIDER = VectorStoreProviderType.PINECONE
        mock_settings.PINECONE_API_KEY = "test-key"
        mock_settings.PINECONE_INDEX_NAME = "test-index"

        from app.providers.vectorstore.factory import get_vectorstore_provider

        provider = get_vectorstore_provider()
        assert isinstance(provider, PineconeProvider)

    @patch("app.providers.vectorstore.factory.settings")
    def test_raises_not_implemented_for_qdrant(self, mock_settings):
        mock_settings.VECTORSTORE_PROVIDER = VectorStoreProviderType.QDRANT

        from app.providers.vectorstore.factory import get_vectorstore_provider

        with pytest.raises(NotImplementedError, match="Qdrant"):
            get_vectorstore_provider()

    @patch("app.providers.vectorstore.factory.settings")
    def test_raises_not_implemented_for_pgvector(self, mock_settings):
        mock_settings.VECTORSTORE_PROVIDER = VectorStoreProviderType.PGVECTOR

        from app.providers.vectorstore.factory import get_vectorstore_provider

        with pytest.raises(NotImplementedError, match="pgvector"):
            get_vectorstore_provider()

    @patch("app.providers.vectorstore.factory.settings")
    def test_raises_for_unknown_provider(self, mock_settings):
        mock_settings.VECTORSTORE_PROVIDER = "unknown"

        from app.providers.vectorstore.factory import get_vectorstore_provider

        with pytest.raises(ValueError, match="Unknown vector store provider"):
            get_vectorstore_provider()
