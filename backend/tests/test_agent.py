"""Tests for the LangChain stock analysis agent."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.enums import LLMProviderType, SignalType


class TestBuildTools:
    def test_returns_six_tools(self):
        from app.agents.agent import _build_tools

        tools = _build_tools()
        assert len(tools) == 6

    def test_tool_names(self):
        from app.agents.agent import _build_tools

        tools = _build_tools()
        names = {t.name for t in tools}
        assert names == {
            "get_stock_price",
            "calculate_technicals",
            "get_fundamental_analysis",
            "get_news_headlines",
            "analyze_sentiment",
            "search_context",
        }


class TestGetLangchainLlm:
    @patch("app.agents.agent.settings")
    def test_returns_chat_openai_for_openai_provider(self, mock_settings):
        mock_settings.LLM_PROVIDER = LLMProviderType.OPENAI
        mock_settings.OPENAI_API_KEY = "test-key"
        mock_settings.LLM_MODEL = "gpt-4o"

        from app.agents.agent import _get_langchain_llm

        llm = _get_langchain_llm()
        from langchain_openai import ChatOpenAI

        assert isinstance(llm, ChatOpenAI)

    @patch("app.agents.agent.settings")
    def test_returns_chat_anthropic_for_anthropic_provider(self, mock_settings):
        mock_settings.LLM_PROVIDER = LLMProviderType.ANTHROPIC
        mock_settings.ANTHROPIC_API_KEY = "test-key"
        mock_settings.LLM_MODEL = "claude-3-5-haiku-20241022"

        from app.agents.agent import _get_langchain_llm

        llm = _get_langchain_llm()
        from langchain_anthropic import ChatAnthropic

        assert isinstance(llm, ChatAnthropic)


class TestParseAgentOutput:
    def test_parses_valid_json(self):
        from app.agents.agent import _parse_agent_output

        output = json.dumps({
            "signal": "BUY",
            "confidence": 0.85,
            "explanation": "Strong bullish signals.",
        })
        result = _parse_agent_output(output)
        assert result.signal == SignalType.BUY
        assert result.confidence == 0.85
        assert result.explanation == "Strong bullish signals."

    def test_falls_back_on_invalid_json(self):
        from app.agents.agent import _parse_agent_output

        result = _parse_agent_output("This is not JSON at all")
        assert result.signal == SignalType.HOLD
        assert result.confidence == 0.5
        assert result.explanation == "This is not JSON at all"

    def test_clamps_confidence_to_range(self):
        from app.agents.agent import _parse_agent_output

        output = json.dumps({"signal": "BUY", "confidence": 1.5})
        result = _parse_agent_output(output)
        assert result.confidence == 1.0

        output = json.dumps({"signal": "SELL", "confidence": -0.3})
        result = _parse_agent_output(output)
        assert result.confidence == 0.0

    def test_invalid_signal_defaults_to_hold(self):
        from app.agents.agent import _parse_agent_output

        output = json.dumps({"signal": "MAYBE", "confidence": 0.5})
        result = _parse_agent_output(output)
        assert result.signal == SignalType.HOLD


class TestToolWrappers:
    @patch("app.agents.agent.get_stock_price")
    @patch("app.agents.agent.get_ticker")
    def test_stock_price_wrapper_returns_json(self, mock_get_ticker, mock_fn):
        mock_stock = MagicMock()
        mock_get_ticker.return_value = mock_stock
        mock_fn.return_value = MagicMock(model_dump_json=MagicMock(return_value='{"current":150}'))

        from app.agents.agent import _tool_get_stock_price

        result = _tool_get_stock_price("AAPL")
        assert result == '{"current":150}'
        mock_fn.assert_called_once_with(mock_stock)

    @patch("app.agents.agent.get_stock_price", side_effect=ValueError("No data"))
    @patch("app.agents.agent.get_ticker")
    def test_stock_price_wrapper_handles_error(self, mock_get_ticker, mock_fn):
        mock_get_ticker.return_value = MagicMock()

        from app.agents.agent import _tool_get_stock_price

        result = _tool_get_stock_price("INVALID")
        assert "Error" in result
        assert "No data" in result

    @patch("app.agents.agent.calculate_technicals")
    @patch("app.agents.agent.get_ticker")
    def test_technicals_wrapper_returns_json(self, mock_get_ticker, mock_fn):
        mock_stock = MagicMock()
        mock_get_ticker.return_value = mock_stock
        mock_fn.return_value = MagicMock(model_dump_json=MagicMock(return_value='{"rsi":55}'))

        from app.agents.agent import _tool_calculate_technicals

        result = _tool_calculate_technicals("AAPL")
        assert result == '{"rsi":55}'

    @patch("app.agents.agent.calculate_fundamentals")
    @patch("app.agents.agent.get_ticker")
    def test_fundamentals_wrapper_returns_json(self, mock_get_ticker, mock_fn):
        mock_stock = MagicMock()
        mock_get_ticker.return_value = mock_stock
        mock_fn.return_value = MagicMock(model_dump_json=MagicMock(return_value='{"pe_ratio":25}'))

        from app.agents.agent import _tool_get_fundamentals

        result = _tool_get_fundamentals("AAPL")
        assert result == '{"pe_ratio":25}'

    @patch("app.agents.agent.get_news_headlines", return_value="1. Headline")
    def test_news_wrapper_returns_string(self, mock_fn):
        from app.agents.agent import _tool_get_news_headlines

        result = _tool_get_news_headlines("AAPL")
        assert result == "1. Headline"

    @pytest.mark.asyncio
    @patch("app.agents.agent.analyze_sentiment", new_callable=AsyncMock)
    @patch("app.agents.agent.fetch_news_headlines")
    async def test_sentiment_wrapper_fetches_and_analyzes(self, mock_news, mock_sentiment):
        mock_news.return_value = ["headline1"]
        mock_sentiment.return_value = MagicMock(
            model_dump_json=MagicMock(return_value='{"overall":"positive","score":0.8}')
        )

        from app.agents.agent import _tool_analyze_sentiment

        result = await _tool_analyze_sentiment("AAPL")
        assert '"positive"' in result
        mock_news.assert_called_once_with("AAPL")
        mock_sentiment.assert_called_once_with(["headline1"])

    @pytest.mark.asyncio
    @patch("app.agents.agent.retrieve_context", new_callable=AsyncMock, return_value="RSI context")
    async def test_search_context_wrapper(self, mock_retrieve):
        from app.agents.agent import _tool_search_context

        result = await _tool_search_context("RSI oversold")
        assert result == "RSI context"
        mock_retrieve.assert_called_once_with("RSI oversold")


class TestRunAgent:
    @pytest.mark.asyncio
    @patch("app.agents.agent.create_agent")
    @patch("app.agents.agent._get_langchain_llm")
    async def test_happy_path(self, mock_llm_factory, mock_create_agent):
        mock_llm_factory.return_value = MagicMock()

        agent_response = json.dumps({
            "signal": "BUY",
            "confidence": 0.85,
            "explanation": "Strong technicals and positive sentiment.",
        })
        mock_graph = MagicMock()
        mock_graph.ainvoke = AsyncMock(return_value={
            "messages": [MagicMock(content=agent_response)],
        })
        mock_create_agent.return_value = mock_graph

        from app.agents.agent import run_agent

        result = await run_agent("AAPL")

        assert result.signal == SignalType.BUY
        assert result.confidence == 0.85
        assert "Strong technicals" in result.explanation

    @pytest.mark.asyncio
    @patch("app.agents.agent.create_agent")
    @patch("app.agents.agent._get_langchain_llm")
    async def test_invalid_json_fallback(self, mock_llm_factory, mock_create_agent):
        mock_llm_factory.return_value = MagicMock()

        mock_graph = MagicMock()
        mock_graph.ainvoke = AsyncMock(return_value={
            "messages": [MagicMock(content="I couldn't parse my response properly")],
        })
        mock_create_agent.return_value = mock_graph

        from app.agents.agent import run_agent

        result = await run_agent("AAPL")

        assert result.signal == SignalType.HOLD
        assert result.confidence == 0.5
        assert "couldn't parse" in result.explanation
