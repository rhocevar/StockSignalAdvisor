"""Seed Pinecone index with financial analysis context documents.

Creates the Pinecone index if it doesn't exist, generates embeddings for
seed documents, and upserts them into the index.

Usage:
    cd backend && python -m scripts.seed_pinecone
"""

import asyncio
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

from pinecone import Pinecone  # noqa: E402

from app.config import settings  # noqa: E402
from app.enums import DocumentType  # noqa: E402
from app.providers.vectorstore.base import Document  # noqa: E402
from app.providers.vectorstore.factory import get_vectorstore_provider  # noqa: E402
from app.rag.embeddings import embed_documents  # noqa: E402

_INDEX_DIMENSION = 1536
_INDEX_METRIC = "cosine"
_INDEX_READY_POLL_SECONDS = 2
_INDEX_READY_TIMEOUT_SECONDS = 60

# ---------------------------------------------------------------------------
# Seed documents — financial analysis context for the RAG system
# ---------------------------------------------------------------------------
SEED_DOCUMENTS: list[Document] = [
    # Technical analysis patterns
    Document(
        id="ta-rsi-oversold",
        content="When the Relative Strength Index (RSI) drops below 30, the stock "
        "is considered oversold and may be due for a price rebound. This is a "
        "bullish technical signal, especially when combined with increasing volume.",
        doc_type=DocumentType.ANALYSIS,
    ),
    Document(
        id="ta-rsi-overbought",
        content="When RSI rises above 70, the stock is considered overbought and may "
        "face selling pressure. This is a bearish signal suggesting the stock could "
        "pull back in the near term.",
        doc_type=DocumentType.ANALYSIS,
    ),
    Document(
        id="ta-macd-bullish",
        content="A bullish MACD crossover occurs when the MACD line crosses above "
        "the signal line. This suggests upward momentum is building and is often "
        "used as a buy signal by technical traders.",
        doc_type=DocumentType.ANALYSIS,
    ),
    Document(
        id="ta-macd-bearish",
        content="A bearish MACD crossover happens when the MACD line falls below "
        "the signal line, indicating downward momentum. Traders often interpret "
        "this as a sell or reduce signal.",
        doc_type=DocumentType.ANALYSIS,
    ),
    Document(
        id="ta-sma-golden-cross",
        content="A golden cross occurs when the 50-day SMA crosses above the "
        "200-day SMA, signaling a potential long-term bullish trend. This is one "
        "of the most watched technical indicators by institutional investors.",
        doc_type=DocumentType.ANALYSIS,
    ),
    Document(
        id="ta-sma-death-cross",
        content="A death cross occurs when the 50-day SMA crosses below the "
        "200-day SMA, signaling a potential long-term bearish trend. It often "
        "triggers selling from trend-following algorithms.",
        doc_type=DocumentType.ANALYSIS,
    ),
    Document(
        id="ta-volume-confirmation",
        content="Volume confirms price movements. A price breakout on high volume "
        "is more reliable than one on low volume. Always check if volume supports "
        "the direction of the trend before acting on technical signals.",
        doc_type=DocumentType.ANALYSIS,
    ),
    # Fundamental analysis guidelines
    Document(
        id="fa-pe-ratio",
        content="The Price-to-Earnings (P/E) ratio measures how much investors are "
        "willing to pay per dollar of earnings. A P/E below the sector average may "
        "indicate undervaluation, while a high P/E could suggest overvaluation or "
        "high growth expectations.",
        doc_type=DocumentType.ANALYSIS,
    ),
    Document(
        id="fa-peg-ratio",
        content="A PEG ratio below 1.0 suggests the stock may be undervalued "
        "relative to its earnings growth rate. A PEG above 2.0 may indicate "
        "overvaluation. The PEG ratio is especially useful for comparing growth "
        "stocks with different P/E ratios.",
        doc_type=DocumentType.ANALYSIS,
    ),
    Document(
        id="fa-debt-to-equity",
        content="The debt-to-equity ratio measures financial leverage. A ratio "
        "above 2.0 may indicate high financial risk, especially for non-financial "
        "companies. Low debt companies have more flexibility during economic "
        "downturns.",
        doc_type=DocumentType.ANALYSIS,
    ),
    Document(
        id="fa-profit-margins",
        content="Consistently high profit margins indicate a competitive moat. "
        "Compare margins to industry peers — a company with significantly higher "
        "margins likely has pricing power or cost advantages that protect against "
        "competition.",
        doc_type=DocumentType.ANALYSIS,
    ),
    Document(
        id="fa-revenue-growth",
        content="Revenue growth rate above 15% year-over-year is generally "
        "considered strong for large-cap stocks. However, always check if growth "
        "is organic or driven by acquisitions, as organic growth is more "
        "sustainable.",
        doc_type=DocumentType.ANALYSIS,
    ),
    # Sector-specific guidance
    Document(
        id="sector-tech-pe",
        content="Technology stocks typically trade at higher P/E ratios (25-40x) "
        "compared to the broader market (15-20x) due to higher growth expectations. "
        "Evaluate tech stocks primarily on revenue growth, margins, and total "
        "addressable market rather than P/E alone.",
        doc_type=DocumentType.ANALYSIS,
    ),
    Document(
        id="sector-utilities",
        content="Utility stocks are defensive investments valued primarily for "
        "stable dividends. A dividend yield above 4% with a payout ratio below "
        "80% suggests a sustainable and attractive yield. These stocks tend to "
        "outperform during market downturns.",
        doc_type=DocumentType.ANALYSIS,
    ),
    Document(
        id="sector-financials",
        content="Financial stocks (banks, insurance) should be evaluated using "
        "price-to-book (P/B) ratio rather than P/E. A P/B below 1.0 may indicate "
        "undervaluation, but also check return on equity (ROE) — healthy banks "
        "typically maintain ROE above 10%.",
        doc_type=DocumentType.ANALYSIS,
    ),
    # Risk assessment
    Document(
        id="risk-beta",
        content="Beta measures a stock's volatility relative to the market. A beta "
        "above 1.5 indicates high volatility — the stock moves 50% more than the "
        "market. Conservative investors should prefer stocks with beta between "
        "0.5 and 1.2.",
        doc_type=DocumentType.ANALYSIS,
    ),
    Document(
        id="risk-diversification",
        content="When analyzing a stock, always consider how it fits into portfolio "
        "diversification. Avoid recommending a BUY if the stock is highly "
        "correlated with the investor's existing holdings. Sector concentration "
        "above 30% increases portfolio risk significantly.",
        doc_type=DocumentType.ANALYSIS,
    ),
    Document(
        id="risk-52w-range",
        content="A stock trading within 5% of its 52-week high may face resistance, "
        "while a stock near its 52-week low could be a value opportunity or a "
        "falling knife. Check fundamentals and news to distinguish between the two.",
        doc_type=DocumentType.ANALYSIS,
    ),
]


def _ensure_index_exists(api_key: str, index_name: str) -> None:
    """Create the Pinecone index if it doesn't already exist."""
    pc = Pinecone(api_key=api_key)
    existing = [idx.name for idx in pc.list_indexes()]

    if index_name in existing:
        print(f"Index '{index_name}' already exists — skipping creation.")
        return

    print(f"Creating index '{index_name}' (dim={_INDEX_DIMENSION}, metric={_INDEX_METRIC})...")
    pc.create_index(
        name=index_name,
        dimension=_INDEX_DIMENSION,
        metric=_INDEX_METRIC,
        spec={"serverless": {"cloud": "aws", "region": "us-east-1"}},
    )

    # Wait for the index to be ready
    start = time.time()
    while True:
        description = pc.describe_index(index_name)
        if description.status.get("ready", False):
            print(f"Index ready in {time.time() - start:.1f}s.")
            return
        if time.time() - start > _INDEX_READY_TIMEOUT_SECONDS:
            print("Warning: index not ready within timeout, proceeding anyway.")
            return
        time.sleep(_INDEX_READY_POLL_SECONDS)


async def seed() -> None:
    """Main seed workflow: create index, generate embeddings, upsert."""
    api_key = settings.PINECONE_API_KEY
    index_name = settings.PINECONE_INDEX_NAME

    if not api_key:
        print("Error: PINECONE_API_KEY is not set.")
        sys.exit(1)

    # Step 1: Ensure index exists
    _ensure_index_exists(api_key, index_name)

    # Step 2: Generate embeddings for all seed documents
    print(f"Generating embeddings for {len(SEED_DOCUMENTS)} documents...")
    documents = await embed_documents(SEED_DOCUMENTS)
    print("Embeddings generated.")

    # Step 3: Upsert via provider
    provider = get_vectorstore_provider()
    count = await provider.upsert(documents)
    print(f"Upserted {count} documents into '{index_name}'.")

    # Step 4: Summary
    print("\nSeed complete!")
    print(f"  Index: {index_name}")
    print(f"  Documents: {count}")
    print(f"  Dimension: {_INDEX_DIMENSION}")
    print(f"  Metric: {_INDEX_METRIC}")


if __name__ == "__main__":
    asyncio.run(seed())
