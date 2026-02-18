"""Semantic search retriever — queries the vector store with natural language."""

from app.enums import DocumentType
from app.providers.vectorstore.base import SearchResult
from app.providers.vectorstore.factory import get_vectorstore_provider
from app.rag.embeddings import generate_embedding


async def retrieve(
    query: str,
    top_k: int = 5,
    doc_type: DocumentType | None = None,
) -> list[SearchResult]:
    """Search the vector store for documents similar to the query.

    Args:
        query: Natural language search query.
        top_k: Maximum number of results to return.
        doc_type: Optional filter to restrict results to a specific document type.

    Returns:
        List of SearchResult objects ordered by relevance score.
    """
    query_embedding = await generate_embedding(query)

    metadata_filter = None
    if doc_type is not None:
        metadata_filter = {"doc_type": {"$eq": doc_type.value}}

    provider = get_vectorstore_provider()
    return await provider.search(query_embedding, top_k=top_k, filter=metadata_filter)


async def retrieve_context(query: str, top_k: int = 5) -> str:
    """Retrieve relevant context formatted as a readable string for LLM consumption.

    This is the function the LangChain agent's ``search_context`` tool will wrap.
    """
    results = await retrieve(query, top_k=top_k)

    if not results:
        return "No relevant context found for this query."

    lines = []
    for i, result in enumerate(results, 1):
        lines.append(f"{i}. [score={result.score:.2f}] {result.content}")

    return "\n".join(lines)
