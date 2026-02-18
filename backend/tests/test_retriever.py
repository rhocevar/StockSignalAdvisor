"""Tests for the semantic search retriever."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.enums import DocumentType
from app.providers.vectorstore.base import SearchResult


_FAKE_EMBEDDING = [0.1] * 1536

_SAMPLE_RESULTS = [
    SearchResult(
        id="doc-1",
        content="RSI below 30 indicates oversold conditions.",
        score=0.92,
        metadata={"doc_type": "analysis"},
    ),
    SearchResult(
        id="doc-2",
        content="PEG ratio below 1.0 suggests undervaluation.",
        score=0.85,
        metadata={"doc_type": "analysis"},
    ),
]


def _mock_llm_provider():
    provider = MagicMock()
    provider.embed = AsyncMock(return_value=_FAKE_EMBEDDING)
    return provider


def _mock_vectorstore_provider(results: list[SearchResult] | None = None):
    provider = MagicMock()
    provider.search = AsyncMock(return_value=results if results is not None else [])
    return provider


class TestRetrieve:
    @pytest.mark.asyncio
    @patch("app.rag.retriever.get_vectorstore_provider")
    @patch("app.rag.embeddings.get_llm_provider")
    async def test_returns_search_results(self, mock_llm_factory, mock_vs_factory):
        mock_llm_factory.return_value = _mock_llm_provider()
        mock_vs_factory.return_value = _mock_vectorstore_provider(_SAMPLE_RESULTS)

        from app.rag.retriever import retrieve

        results = await retrieve("What does RSI mean?")

        assert len(results) == 2
        assert results[0].id == "doc-1"
        assert results[0].score == 0.92

    @pytest.mark.asyncio
    @patch("app.rag.retriever.get_vectorstore_provider")
    @patch("app.rag.embeddings.get_llm_provider")
    async def test_passes_doc_type_filter(self, mock_llm_factory, mock_vs_factory):
        mock_llm_factory.return_value = _mock_llm_provider()
        vs = _mock_vectorstore_provider(_SAMPLE_RESULTS)
        mock_vs_factory.return_value = vs

        from app.rag.retriever import retrieve

        await retrieve("query", doc_type=DocumentType.NEWS)

        vs.search.assert_called_once()
        call_kwargs = vs.search.call_args
        assert call_kwargs[1]["filter"] == {"doc_type": {"$eq": "news"}}

    @pytest.mark.asyncio
    @patch("app.rag.retriever.get_vectorstore_provider")
    @patch("app.rag.embeddings.get_llm_provider")
    async def test_no_filter_when_doc_type_is_none(self, mock_llm_factory, mock_vs_factory):
        mock_llm_factory.return_value = _mock_llm_provider()
        vs = _mock_vectorstore_provider([])
        mock_vs_factory.return_value = vs

        from app.rag.retriever import retrieve

        await retrieve("query")

        call_kwargs = vs.search.call_args
        assert call_kwargs[1]["filter"] is None

    @pytest.mark.asyncio
    @patch("app.rag.retriever.get_vectorstore_provider")
    @patch("app.rag.embeddings.get_llm_provider")
    async def test_empty_results(self, mock_llm_factory, mock_vs_factory):
        mock_llm_factory.return_value = _mock_llm_provider()
        mock_vs_factory.return_value = _mock_vectorstore_provider([])

        from app.rag.retriever import retrieve

        results = await retrieve("obscure query")
        assert results == []


class TestRetrieveContext:
    @pytest.mark.asyncio
    @patch("app.rag.retriever.get_vectorstore_provider")
    @patch("app.rag.embeddings.get_llm_provider")
    async def test_formats_results_as_string(self, mock_llm_factory, mock_vs_factory):
        mock_llm_factory.return_value = _mock_llm_provider()
        mock_vs_factory.return_value = _mock_vectorstore_provider(_SAMPLE_RESULTS)

        from app.rag.retriever import retrieve_context

        text = await retrieve_context("RSI analysis")

        assert "1. [score=0.92]" in text
        assert "RSI below 30" in text
        assert "2. [score=0.85]" in text
        assert "PEG ratio" in text

    @pytest.mark.asyncio
    @patch("app.rag.retriever.get_vectorstore_provider")
    @patch("app.rag.embeddings.get_llm_provider")
    async def test_no_results_returns_message(self, mock_llm_factory, mock_vs_factory):
        mock_llm_factory.return_value = _mock_llm_provider()
        mock_vs_factory.return_value = _mock_vectorstore_provider([])

        from app.rag.retriever import retrieve_context

        text = await retrieve_context("nothing relevant")

        assert "No relevant context found" in text
