import React from "react";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useAnalysis } from "@/hooks/useAnalysis";
import { analyzeStock, ApiError } from "@/lib/api";
import type { AnalyzeResponse } from "@/types";

// Keep ApiError as a real class so instanceof checks work in the retry callback.
jest.mock("../../lib/api", () => ({
  ...jest.requireActual("../../lib/api"),
  analyzeStock: jest.fn(),
}));

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
    defaultOptions: { queries: { retry: false } },
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

  it("starts loading immediately when ticker is provided", () => {
    mockAnalyzeStock.mockResolvedValue(mockResponse);
    const { result } = renderHook(() => useAnalysis("AAPL"), {
      wrapper: createWrapper(),
    });
    expect(result.current.isPending).toBe(true);
    expect(result.current.data).toBeUndefined();
    expect(result.current.error).toBeNull();
  });

  it("returns parsed response on successful query", async () => {
    mockAnalyzeStock.mockResolvedValue(mockResponse);
    const { result } = renderHook(() => useAnalysis("AAPL"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.data).toEqual(mockResponse);
    });

    expect(mockAnalyzeStock).toHaveBeenCalledWith({ ticker: "AAPL" });
    expect(result.current.error).toBeNull();
  });

  it("exposes error when query rejects", async () => {
    const err = new ApiError('Ticker "INVALID" not found.', 404);
    mockAnalyzeStock.mockRejectedValue(err);
    const { result } = renderHook(() => useAnalysis("INVALID"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.error).toEqual(err);
    });

    expect(result.current.data).toBeUndefined();
  });

  it("does not fetch when ticker is empty", () => {
    const { result } = renderHook(() => useAnalysis(""), {
      wrapper: createWrapper(),
    });
    // enabled: false — no fetch should fire
    expect(mockAnalyzeStock).not.toHaveBeenCalled();
    expect(result.current.data).toBeUndefined();
  });
});
