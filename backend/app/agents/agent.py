"""LangChain agent for stock analysis.

Uses a ReAct-style agent with LangChain tools to gather stock data
(price, technicals, fundamentals, news, sentiment, RAG context) and
produce a BUY/HOLD/SELL recommendation.
"""

import json
import logging

from langchain.agents import create_agent
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from langchain_core.tools import Tool
from langchain_openai import ChatOpenAI

from app.agents.prompts import ANALYSIS_SYSTEM_PROMPT
from app.agents.tools.fundamentals import calculate_fundamentals
from app.agents.tools.news_fetcher import fetch_news_headlines, get_news_headlines
from app.agents.tools.sentiment import analyze_sentiment
from app.agents.tools.stock_data import get_stock_price, get_ticker
from app.agents.tools.technical import calculate_technicals
from app.config import settings
from app.enums import AnthropicModel, LLMProviderType, OpenAIModel, SignalType
from app.models.domain import AgentResult
from app.rag.retriever import retrieve_context

logger = logging.getLogger(__name__)

_DEFAULT_TEMPERATURE = 0.3
_MAX_AGENT_ITERATIONS = 10


def _get_langchain_llm() -> ChatOpenAI | ChatAnthropic:
    """Create a LangChain chat model based on the configured provider."""
    if settings.LLM_PROVIDER == LLMProviderType.OPENAI:
        return ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model=settings.LLM_MODEL or OpenAIModel.GPT_4O_MINI,
            temperature=_DEFAULT_TEMPERATURE,
        )
    elif settings.LLM_PROVIDER == LLMProviderType.ANTHROPIC:
        return ChatAnthropic(
            api_key=settings.ANTHROPIC_API_KEY,
            model=settings.LLM_MODEL or AnthropicModel.CLAUDE_3_5_HAIKU,
            temperature=_DEFAULT_TEMPERATURE,
        )
    else:
        raise ValueError(f"Unsupported LLM provider for agent: {settings.LLM_PROVIDER}")


# ---------------------------------------------------------------------------
# Tool wrappers — catch errors and return strings
# ---------------------------------------------------------------------------


def _tool_get_stock_price(ticker: str) -> str:
    """Fetch current price data for a stock ticker."""
    try:
        stock = get_ticker(ticker.upper())
        result = get_stock_price(stock)
        return result.model_dump_json()
    except Exception as e:
        return f"Error fetching stock price: {e}"


def _tool_calculate_technicals(ticker: str) -> str:
    """Calculate technical indicators (RSI, SMA, MACD, volume) for a stock ticker."""
    try:
        stock = get_ticker(ticker.upper())
        result = calculate_technicals(stock)
        return result.model_dump_json()
    except Exception as e:
        return f"Error calculating technicals: {e}"


def _tool_get_fundamentals(ticker: str) -> str:
    """Get fundamental analysis (P/E, market cap, margins, growth) for a stock ticker."""
    try:
        stock = get_ticker(ticker.upper())
        result = calculate_fundamentals(stock)
        return result.model_dump_json()
    except Exception as e:
        return f"Error fetching fundamentals: {e}"


def _tool_get_news_headlines(ticker: str) -> str:
    """Fetch recent news headlines for a stock ticker."""
    try:
        return get_news_headlines(ticker.upper())
    except Exception as e:
        return f"Error fetching news: {e}"


async def _tool_analyze_sentiment(ticker: str) -> str:
    """Fetch news and analyze overall sentiment for a stock ticker."""
    try:
        headlines = fetch_news_headlines(ticker.upper())
        result = await analyze_sentiment(headlines)
        return result.model_dump_json()
    except Exception as e:
        return f"Error analyzing sentiment: {e}"


async def _tool_search_context(query: str) -> str:
    """Search the financial knowledge base for relevant analysis context."""
    try:
        return await retrieve_context(query)
    except Exception as e:
        return f"Error searching context: {e}"


def _build_tools() -> list[Tool]:
    """Build the list of LangChain tools for the stock analysis agent."""
    return [
        Tool(
            name="get_stock_price",
            func=_tool_get_stock_price,
            description=(
                "Fetch current price data for a stock ticker. "
                "Input: ticker symbol (e.g. 'AAPL'). "
                "Returns JSON with current price and change percentages."
            ),
        ),
        Tool(
            name="calculate_technicals",
            func=_tool_calculate_technicals,
            description=(
                "Calculate technical indicators for a stock ticker. "
                "Input: ticker symbol (e.g. 'AAPL'). "
                "Returns JSON with RSI, SMA, MACD, volume trend, and technical score."
            ),
        ),
        Tool(
            name="get_fundamental_analysis",
            func=_tool_get_fundamentals,
            description=(
                "Get fundamental analysis for a stock ticker. "
                "Input: ticker symbol (e.g. 'AAPL'). "
                "Returns JSON with P/E, market cap, margins, growth, and fundamental score."
            ),
        ),
        Tool(
            name="get_news_headlines",
            func=_tool_get_news_headlines,
            description=(
                "Fetch recent news headlines for a stock ticker. "
                "Input: ticker symbol (e.g. 'AAPL'). "
                "Returns formatted list of recent headlines."
            ),
        ),
        Tool(
            name="analyze_sentiment",
            func=_tool_analyze_sentiment,
            coroutine=_tool_analyze_sentiment,
            description=(
                "Fetch news and analyze overall sentiment for a stock ticker. "
                "Input: ticker symbol (e.g. 'AAPL'). "
                "Returns JSON with sentiment classification and score."
            ),
        ),
        Tool(
            name="search_context",
            func=_tool_search_context,
            coroutine=_tool_search_context,
            description=(
                "Search the financial knowledge base for relevant analysis context. "
                "Input: natural language query (e.g. 'RSI oversold signals'). "
                "Returns relevant financial analysis passages."
            ),
        ),
    ]


def _parse_agent_output(output: str) -> AgentResult:
    """Parse the agent's final output into a structured AgentResult.

    Attempts to extract JSON with signal, confidence, and explanation.
    Falls back to HOLD/0.5 if parsing fails.
    """
    try:
        parsed = json.loads(output, strict=False)
        signal_str = parsed.get("signal", SignalType.HOLD.value).upper()
        try:
            signal = SignalType(signal_str)
        except ValueError:
            signal = SignalType.HOLD

        confidence = float(parsed.get("confidence", 0.5))
        confidence = max(0.0, min(1.0, confidence))

        explanation = parsed.get("explanation", output)

        return AgentResult(
            signal=signal,
            confidence=confidence,
            explanation=explanation,
        )
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        logger.warning("Failed to parse agent output as JSON: %s", e)
        return AgentResult(explanation=output)


async def run_agent(ticker: str) -> AgentResult:
    """Run the stock analysis agent for a given ticker."""
    llm = _get_langchain_llm()
    tools = _build_tools()

    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=ANALYSIS_SYSTEM_PROMPT,
    )

    user_message = (
        f"Analyze the stock {ticker} and provide a BUY/HOLD/SELL recommendation "
        f"with confidence score and explanation. Use the available tools to gather "
        f"price data, technical indicators, fundamentals, news, and sentiment. "
        f"Also search the knowledge base for relevant financial analysis context."
    )

    result = await agent.ainvoke(
        {"messages": [HumanMessage(content=user_message)]},
        config={"recursion_limit": _MAX_AGENT_ITERATIONS * 2},
    )

    final_message = result["messages"][-1]
    return _parse_agent_output(final_message.content)
