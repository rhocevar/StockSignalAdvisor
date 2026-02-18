"""Tests for the document indexer."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.enums import DocumentType
from app.providers.vectorstore.base import Document


_FAKE_EMBEDDING = [0.1] * 1536


def _make_doc(doc_id: str, embedding: list[float] | None = None) -> Document:
    return Document(
        id=doc_id,
        content=f"Content for {doc_id}",
        doc_type=DocumentType.ANALYSIS,
        embedding=embedding,
    )


def _mock_llm_provider():
    provider = MagicMock()
    provider.embed = AsyncMock(return_value=_FAKE_EMBEDDING)
    return provider


def _mock_vectorstore_provider(upsert_count: int = 0, delete_count: int = 0):
    provider = MagicMock()
    provider.upsert = AsyncMock(return_value=upsert_count)
    provider.delete = AsyncMock(return_value=delete_count)
    return provider


class TestIndexDocuments:
    @pytest.mark.asyncio
    @patch("app.rag.indexer.get_vectorstore_provider")
    @patch("app.rag.embeddings.get_llm_provider")
    async def test_embeds_and_upserts(self, mock_llm_factory, mock_vs_factory):
        mock_llm_factory.return_value = _mock_llm_provider()
        vs = _mock_vectorstore_provider(upsert_count=2)
        mock_vs_factory.return_value = vs

        from app.rag.indexer import index_documents

        docs = [_make_doc("doc-1"), _make_doc("doc-2")]
        count = await index_documents(docs)

        assert count == 2
        vs.upsert.assert_called_once_with(docs)

    @pytest.mark.asyncio
    @patch("app.rag.indexer.get_vectorstore_provider")
    @patch("app.rag.embeddings.get_llm_provider")
    async def test_skips_existing_embeddings(self, mock_llm_factory, mock_vs_factory):
        llm = _mock_llm_provider()
        mock_llm_factory.return_value = llm
        mock_vs_factory.return_value = _mock_vectorstore_provider(upsert_count=2)

        from app.rag.indexer import index_documents

        docs = [
            _make_doc("already", embedding=[0.5] * 1536),
            _make_doc("needs-embed"),
        ]
        await index_documents(docs)

        # Only the doc without embedding should call embed
        llm.embed.assert_called_once_with("Content for needs-embed")

    @pytest.mark.asyncio
    async def test_empty_list_returns_zero(self):
        from app.rag.indexer import index_documents

        count = await index_documents([])
        assert count == 0


class TestIndexDocument:
    @pytest.mark.asyncio
    @patch("app.rag.indexer.get_vectorstore_provider")
    @patch("app.rag.embeddings.get_llm_provider")
    async def test_single_document(self, mock_llm_factory, mock_vs_factory):
        mock_llm_factory.return_value = _mock_llm_provider()
        vs = _mock_vectorstore_provider(upsert_count=1)
        mock_vs_factory.return_value = vs

        from app.rag.indexer import index_document

        doc = _make_doc("single")
        count = await index_document(doc)

        assert count == 1
        vs.upsert.assert_called_once()


class TestDeleteDocuments:
    @pytest.mark.asyncio
    @patch("app.rag.indexer.get_vectorstore_provider")
    async def test_deletes_and_returns_count(self, mock_vs_factory):
        vs = _mock_vectorstore_provider(delete_count=3)
        mock_vs_factory.return_value = vs

        from app.rag.indexer import delete_documents

        count = await delete_documents(["id-1", "id-2", "id-3"])

        assert count == 3
        vs.delete.assert_called_once_with(["id-1", "id-2", "id-3"])

    @pytest.mark.asyncio
    async def test_empty_ids_returns_zero(self):
        from app.rag.indexer import delete_documents

        count = await delete_documents([])
        assert count == 0
