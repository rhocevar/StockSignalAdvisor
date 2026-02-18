"""Embedding generation pipeline wrapping the LLM provider's embed() method."""

from app.providers.llm.factory import get_llm_provider
from app.providers.vectorstore.base import Document

_DEFAULT_BATCH_SIZE = 20


async def generate_embedding(text: str) -> list[float]:
    """Generate an embedding vector for a single text string."""
    provider = get_llm_provider()
    return await provider.embed(text)


async def generate_embeddings(
    texts: list[str], batch_size: int = _DEFAULT_BATCH_SIZE
) -> list[list[float]]:
    """Generate embeddings for multiple texts in batches.

    Processes texts in chunks of ``batch_size`` to avoid rate limits.
    Returns embeddings in the same order as the input texts.
    """
    if not texts:
        return []

    provider = get_llm_provider()
    embeddings: list[list[float]] = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        batch_embeddings = [await provider.embed(text) for text in batch]
        embeddings.extend(batch_embeddings)

    return embeddings


async def embed_documents(documents: list[Document]) -> list[Document]:
    """Fill in embeddings on Document objects that don't already have one.

    Documents that already have an embedding are left unchanged.
    Returns the same list with embeddings populated.
    """
    if not documents:
        return documents

    provider = get_llm_provider()

    for doc in documents:
        if doc.embedding is None:
            doc.embedding = await provider.embed(doc.content)

    return documents
