from enum import Enum


class ChatMessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class LLMProviderType(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class VectorStoreProviderType(str, Enum):
    PINECONE = "pinecone"
    QDRANT = "qdrant"
    PGVECTOR = "pgvector"


class DocumentType(str, Enum):
    NEWS = "news"
    FINANCIAL_REPORT = "financial_report"
    ANALYSIS = "analysis"
    EARNINGS = "earnings"
    SEC_FILING = "sec_filing"


class OpenAIModel(str, Enum):
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_4O = "gpt-4o"


class OpenAIEmbeddingModel(str, Enum):
    TEXT_EMBEDDING_3_SMALL = "text-embedding-3-small"


class AnthropicModel(str, Enum):
    CLAUDE_3_5_HAIKU = "claude-3-5-haiku-20241022"
    CLAUDE_3_5_SONNET = "claude-3-5-sonnet-20241022"
