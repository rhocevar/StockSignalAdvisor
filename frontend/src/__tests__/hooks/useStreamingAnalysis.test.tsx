import { renderHook, act, waitFor } from "@testing-library/react";
import { useStreamingAnalysis } from "@/hooks/useStreamingAnalysis";
import { streamAnalysis } from "@/lib/api";
import type { SseEvent } from "@/lib/api";
import type { AnalyzeResponse } from "@/types";

jest.mock("../../lib/api", () => ({
  ...jest.requireActual("../../lib/api"),
  streamAnalysis: jest.fn(),
}));

const mockStreamAnalysis = streamAnalysis as jest.Mock;

const mockResult: AnalyzeResponse = {
  ticker: "AAPL",
  company_name: "Apple Inc.",
  signal: "BUY",
  confidence: 0.75,
  explanation: "Strong signals.",
  analysis: { technical: null, fundamentals: null, sentiment: null },
  price_data: null,
  sources: [],
  metadata: {
    generated_at: "2025-01-01T00:00:00Z",
    llm_provider: "openai",
    model_used: "gpt-4o-mini",
    vectorstore_provider: "pinecone",
    cached: false,
  },
};

const technicalData = {
  rsi: 55,
  rsi_interpretation: "neutral",
  sma_50: null,
  sma_200: null,
  price_vs_sma50: null,
  price_vs_sma200: null,
  macd_signal: null,
  volume_trend: null,
  technical_score: 0.6,
};

describe("useStreamingAnalysis", () => {
  afterEach(() => {
    jest.resetAllMocks();
  });

  it("starts with isStreaming true", () => {
    mockStreamAnalysis.mockImplementation(() => new Promise(() => {}));
    const { result } = renderHook(() => useStreamingAnalysis("AAPL"));
    expect(result.current.isStreaming).toBe(true);
    expect(result.current.result).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it("sets technical state when technical event is received", async () => {
    mockStreamAnalysis.mockImplementation(
      async (_ticker: string, onEvent: (e: SseEvent) => void) => {
        onEvent({ type: "technical", data: technicalData });
        await new Promise(() => {}); // keep streaming open
      },
    );
    const { result } = renderHook(() => useStreamingAnalysis("AAPL"));
    await waitFor(() => {
      expect(result.current.technical).toEqual(technicalData);
    });
  });

  it("sets result and clears isStreaming when complete event is received", async () => {
    mockStreamAnalysis.mockImplementation(
      async (_ticker: string, onEvent: (e: SseEvent) => void) => {
        onEvent({ type: "complete", data: mockResult });
      },
    );
    const { result } = renderHook(() => useStreamingAnalysis("AAPL"));
    await waitFor(() => {
      expect(result.current.result).toEqual(mockResult);
      expect(result.current.isStreaming).toBe(false);
    });
  });

  it("sets error and clears isStreaming when error event is received", async () => {
    mockStreamAnalysis.mockImplementation(
      async (_ticker: string, onEvent: (e: SseEvent) => void) => {
        onEvent({ type: "error", data: { code: 404, message: "Ticker not found." } });
      },
    );
    const { result } = renderHook(() => useStreamingAnalysis("AAPL"));
    await waitFor(() => {
      expect(result.current.error).toBe("Ticker not found.");
      expect(result.current.isStreaming).toBe(false);
    });
  });

  it("restart resets state and re-opens the stream", async () => {
    let callCount = 0;
    mockStreamAnalysis.mockImplementation(
      async (_ticker: string, onEvent: (e: SseEvent) => void) => {
        callCount += 1;
        if (callCount === 2) {
          onEvent({ type: "complete", data: mockResult });
        }
      },
    );

    const { result } = renderHook(() => useStreamingAnalysis("AAPL"));

    act(() => {
      result.current.restart();
    });

    await waitFor(() => {
      expect(result.current.result).toEqual(mockResult);
    });
    expect(mockStreamAnalysis).toHaveBeenCalledTimes(2);
  });
});
