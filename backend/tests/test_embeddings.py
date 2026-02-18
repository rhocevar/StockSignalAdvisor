"""Tests for the embedding generation pipeline."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.enums import DocumentType
from app.providers.vectorstore.base import Document


_FAKE_EMBEDDING = [0.1] * 1536


def _mock_provider(embed_return=None):
    """Create a mock LLM provider with a working embed method."""
    provider = MagicMock()
    provider.embed = AsyncMock(return_value=embed_return or _FAKE_EMBEDDING)
    return provider


class TestGenerateEmbedding:
    @pytest.mark.asyncio
    @patch("app.rag.embeddings.get_llm_provider")
    async def test_returns_embedding_vector(self, mock_factory):
        mock_factory.return_value = _mock_provider()

        from app.rag.embeddings import generate_embedding

        result = await generate_embedding("test text")

        assert result == _FAKE_EMBEDDING
        mock_factory.return_value.embed.assert_called_once_with("test text")


class TestGenerateEmbeddings:
    @pytest.mark.asyncio
    @patch("app.rag.embeddings.get_llm_provider")
    async def test_returns_correct_count(self, mock_factory):
        mock_factory.return_value = _mock_provider()

        from app.rag.embeddings import generate_embeddings

        result = await generate_embeddings(["a", "b", "c"])

        assert len(result) == 3
        assert all(v == _FAKE_EMBEDDING for v in result)

    @pytest.mark.asyncio
    @patch("app.rag.embeddings.get_llm_provider")
    async def test_empty_input_returns_empty(self, mock_factory):
        from app.rag.embeddings import generate_embeddings

        result = await generate_embeddings([])

        assert result == []
        mock_factory.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.rag.embeddings.get_llm_provider")
    async def test_respects_batch_size(self, mock_factory):
        provider = _mock_provider()
        mock_factory.return_value = provider

        from app.rag.embeddings import generate_embeddings

        texts = [f"text_{i}" for i in range(5)]
        result = await generate_embeddings(texts, batch_size=2)

        assert len(result) == 5
        # embed() called once per text
        assert provider.embed.call_count == 5


class TestEmbedDocuments:
    @pytest.mark.asyncio
    @patch("app.rag.embeddings.get_llm_provider")
    async def test_fills_in_embeddings(self, mock_factory):
        mock_factory.return_value = _mock_provider()

        from app.rag.embeddings import embed_documents

        docs = [
            Document(id="1", content="hello", doc_type=DocumentType.NEWS),
            Document(id="2", content="world", doc_type=DocumentType.ANALYSIS),
        ]
        result = await embed_documents(docs)

        assert len(result) == 2
        assert all(d.embedding == _FAKE_EMBEDDING for d in result)

    @pytest.mark.asyncio
    @patch("app.rag.embeddings.get_llm_provider")
    async def test_skips_documents_with_existing_embeddings(self, mock_factory):
        provider = _mock_provider()
        mock_factory.return_value = provider

        from app.rag.embeddings import embed_documents

        existing = [0.5] * 1536
        docs = [
            Document(
                id="1",
                content="already embedded",
                doc_type=DocumentType.NEWS,
                embedding=existing,
            ),
            Document(id="2", content="needs embedding", doc_type=DocumentType.ANALYSIS),
        ]
        await embed_documents(docs)

        # Only the second document should have been embedded
        assert docs[0].embedding == existing
        assert docs[1].embedding == _FAKE_EMBEDDING
        provider.embed.assert_called_once_with("needs embedding")

    @pytest.mark.asyncio
    @patch("app.rag.embeddings.get_llm_provider")
    async def test_empty_list_returns_empty(self, mock_factory):
        from app.rag.embeddings import embed_documents

        result = await embed_documents([])

        assert result == []
        mock_factory.assert_not_called()
