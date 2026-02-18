"""Document indexer — generates embeddings and upserts to the vector store."""

from app.providers.vectorstore.base import Document
from app.providers.vectorstore.factory import get_vectorstore_provider
from app.rag.embeddings import embed_documents


async def index_documents(documents: list[Document]) -> int:
    """Embed and upsert documents into the vector store.

    Generates embeddings for documents that don't already have one,
    then upserts all documents into the configured vector store.
    Returns the count of upserted documents.
    """
    if not documents:
        return 0

    await embed_documents(documents)
    provider = get_vectorstore_provider()
    return await provider.upsert(documents)


async def index_document(document: Document) -> int:
    """Embed and upsert a single document into the vector store."""
    return await index_documents([document])


async def delete_documents(ids: list[str]) -> int:
    """Delete documents from the vector store by ID."""
    if not ids:
        return 0

    provider = get_vectorstore_provider()
    return await provider.delete(ids)
