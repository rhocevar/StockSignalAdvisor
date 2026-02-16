from app.config import settings
from app.enums import VectorStoreProviderType
from .base import VectorStoreProvider
from .pinecone import PineconeProvider


def get_vectorstore_provider() -> VectorStoreProvider:
    """Factory function to get the configured vector store provider."""

    if settings.VECTORSTORE_PROVIDER == VectorStoreProviderType.PINECONE:
        return PineconeProvider(
            api_key=settings.PINECONE_API_KEY,
            index_name=settings.PINECONE_INDEX_NAME,
        )
    elif settings.VECTORSTORE_PROVIDER == VectorStoreProviderType.QDRANT:
        raise NotImplementedError("Qdrant provider coming soon")
    elif settings.VECTORSTORE_PROVIDER == VectorStoreProviderType.PGVECTOR:
        raise NotImplementedError("pgvector provider coming soon")
    else:
        raise ValueError(
            f"Unknown vector store provider: {settings.VECTORSTORE_PROVIDER}"
        )
