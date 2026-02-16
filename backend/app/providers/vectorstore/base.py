from abc import ABC, abstractmethod
from typing import Optional

from pydantic import BaseModel

from app.enums import DocumentType


class Document(BaseModel):
    id: str
    content: str
    doc_type: DocumentType
    embedding: Optional[list[float]] = None
    metadata: dict = {}


class SearchResult(BaseModel):
    id: str
    content: str
    score: float
    metadata: dict = {}


class VectorStoreProvider(ABC):
    """Abstract base class for vector store providers."""

    @abstractmethod
    async def upsert(self, documents: list[Document]) -> int:
        """Insert or update documents. Returns count of upserted docs."""
        pass

    @abstractmethod
    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        filter: Optional[dict] = None,
    ) -> list[SearchResult]:
        """Search for similar documents."""
        pass

    @abstractmethod
    async def delete(self, ids: list[str]) -> int:
        """Delete documents by ID. Returns count of deleted docs."""
        pass
