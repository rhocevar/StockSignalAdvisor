import React from "react";
import { renderHook, act, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useAnalysis } from "@/hooks/useAnalysis";
import { analyzeStock } from "@/lib/api";
import type { AnalyzeResponse } from "@/types";

jest.mock("../../lib/api");

const mockAnalyzeStock = analyzeStock as jest.Mock;

const mockResponse: AnalyzeResponse = {
  ticker: "AAPL",
  company_name: "Apple Inc.",
  signal: "BUY",
  confidence: 0.85,
  explanation: "Strong technical signals.",
  analysis: { technical: null, fundamentals: null, sentiment: null },
  price_data: {
    current: 150.0,
    currency: "USD",
    change_percent_1d: 1.2,
    change_percent_1w: null,
    change_percent_1m: null,
    high_52w: null,
    low_52w: null,
    price_history: [],
  },
  sources: [],
  metadata: {
    generated_at: "2025-01-01T00:00:00Z",
    llm_provider: "openai",
    model_used: "gpt-4o-mini",
    vectorstore_provider: "pinecone",
    cached: false,
  },
};

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { mutations: { retry: false } },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  };
}

describe("useAnalysis", () => {
  afterEach(() => {
    jest.resetAllMocks();
  });

  it("starts in idle state with no data or error", () => {
    const { result } = renderHook(() => useAnalysis(), {
      wrapper: createWrapper(),
    });
    expect(result.current.isPending).toBe(false);
    expect(result.current.data).toBeUndefined();
    expect(result.current.error).toBeNull();
  });

  it("returns parsed response on successful mutation", async () => {
    mockAnalyzeStock.mockResolvedValue(mockResponse);
    const { result } = renderHook(() => useAnalysis(), {
      wrapper: createWrapper(),
    });

    act(() => {
      result.current.mutate({ ticker: "AAPL" });
    });

    // Use waitFor because mutate() is fire-and-forget — the async work settles
    // after the act() call returns.
    await waitFor(() => {
      expect(result.current.data).toEqual(mockResponse);
    });

    // TanStack Query v5 passes a context object as a second arg to mutationFn;
    // check only the first argument (the caller-supplied variables).
    expect(mockAnalyzeStock.mock.calls[0][0]).toEqual({ ticker: "AAPL" });
    expect(result.current.error).toBeNull();
  });

  it("exposes error when mutation rejects", async () => {
    const err = new Error('Ticker "INVALID" not found.');
    mockAnalyzeStock.mockRejectedValue(err);
    const { result } = renderHook(() => useAnalysis(), {
      wrapper: createWrapper(),
    });

    act(() => {
      result.current.mutate({ ticker: "INVALID" });
    });

    await waitFor(() => {
      expect(result.current.error).toEqual(err);
    });

    expect(result.current.data).toBeUndefined();
  });
});
