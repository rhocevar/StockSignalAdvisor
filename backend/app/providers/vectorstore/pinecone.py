import asyncio
from enum import Enum

from pinecone import Pinecone

from .base import Document, SearchResult, VectorStoreProvider


class PineconeMetadataKey(str, Enum):
    """Keys used in Pinecone vector metadata."""
    CONTENT = "content"
    DOC_TYPE = "doc_type"


class PineconeVectorKey(str, Enum):
    """Keys used in Pinecone vector schema."""
    ID = "id"
    VALUES = "values"
    METADATA = "metadata"


class PineconeResultKey(str, Enum):
    """Keys used in Pinecone query results."""
    MATCHES = "matches"
    ID = "id"
    SCORE = "score"
    METADATA = "metadata"


class PineconeProvider(VectorStoreProvider):
    def __init__(self, api_key: str, index_name: str):
        self.pc = Pinecone(api_key=api_key)
        self.index = self.pc.Index(index_name)

    async def upsert(self, documents: list[Document]) -> int:
        vectors = [
            {
                PineconeVectorKey.ID: doc.id,
                PineconeVectorKey.VALUES: doc.embedding,
                PineconeVectorKey.METADATA: {
                    **doc.metadata,
                    PineconeMetadataKey.CONTENT: doc.content,
                    PineconeMetadataKey.DOC_TYPE: doc.doc_type.value,
                },
            }
            for doc in documents
        ]
        await asyncio.to_thread(self.index.upsert, vectors=vectors)
        return len(vectors)

    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        filter: dict | None = None,
    ) -> list[SearchResult]:
        results = await asyncio.to_thread(
            self.index.query,
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            filter=filter,
        )
        return [
            SearchResult(
                id=match[PineconeResultKey.ID],
                content=match[PineconeResultKey.METADATA].get(
                    PineconeMetadataKey.CONTENT, ""
                ),
                score=match[PineconeResultKey.SCORE],
                metadata=match[PineconeResultKey.METADATA],
            )
            for match in results[PineconeResultKey.MATCHES]
        ]

    async def delete(self, ids: list[str]) -> int:
        await asyncio.to_thread(self.index.delete, ids=ids)
        return len(ids)
