"""LLM-powered sentiment analysis for news headlines."""

import json
import logging

from app.enums import ChatMessageRole, SentimentType
from app.models.domain import NewsSource, SentimentAnalysis
from app.providers.llm.base import ChatMessage
from app.providers.llm.factory import get_llm_provider

from ..prompts import SENTIMENT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

_NEUTRAL_FALLBACK = SentimentAnalysis(
    overall=SentimentType.NEUTRAL,
    score=0.5,
    positive_count=0,
    negative_count=0,
    neutral_count=0,
)

_SENTIMENT_MAP = {
    "positive": SentimentType.POSITIVE,
    "negative": SentimentType.NEGATIVE,
    "neutral": SentimentType.NEUTRAL,
    "mixed": SentimentType.MIXED,
}


async def analyze_sentiment(
    headlines: list[NewsSource],
) -> SentimentAnalysis:
    """Classify news headlines via LLM and return aggregated sentiment.

    Each ``NewsSource.sentiment`` is updated in-place with the per-headline
    classification returned by the LLM.
    """
    if not headlines:
        return _NEUTRAL_FALLBACK.model_copy()

    numbered = "\n".join(
        f"{i}. {h.title}" for i, h in enumerate(headlines)
    )
    user_message = f"Classify the sentiment of these headlines:\n\n{numbered}"

    llm = get_llm_provider()
    response = await llm.complete(
        messages=[
            ChatMessage(role=ChatMessageRole.SYSTEM, content=SENTIMENT_SYSTEM_PROMPT),
            ChatMessage(role=ChatMessageRole.USER, content=user_message),
        ],
        temperature=0.1,
        max_tokens=500,
        json_mode=True,
    )

    try:
        data = json.loads(response.content)
    except (json.JSONDecodeError, TypeError):
        logger.warning("Failed to parse sentiment LLM response as JSON")
        return _NEUTRAL_FALLBACK.model_copy()

    # Count per-headline sentiments and update NewsSource objects in-place
    positive = 0
    negative = 0
    neutral = 0

    for item in data.get("headlines", []):
        idx = item.get("index")
        raw_sentiment = item.get("sentiment", "neutral").lower()
        sentiment_type = _SENTIMENT_MAP.get(raw_sentiment, SentimentType.NEUTRAL)

        if sentiment_type == SentimentType.POSITIVE:
            positive += 1
        elif sentiment_type == SentimentType.NEGATIVE:
            negative += 1
        else:
            neutral += 1

        if isinstance(idx, int) and 0 <= idx < len(headlines):
            headlines[idx].sentiment = sentiment_type

    overall_raw = data.get("overall", "neutral").lower()
    overall = _SENTIMENT_MAP.get(overall_raw, SentimentType.NEUTRAL)

    score = data.get("score")
    if not isinstance(score, (int, float)) or score < 0 or score > 1:
        score = 0.5

    return SentimentAnalysis(
        overall=overall,
        score=round(float(score), 4),
        positive_count=positive,
        negative_count=negative,
        neutral_count=neutral,
    )
