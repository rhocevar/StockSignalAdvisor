import { analyzeStock } from "@/lib/api";
import type { AnalyzeRequest, AnalyzeResponse } from "@/types";

const mockRequest: AnalyzeRequest = { ticker: "AAPL" };

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

function mockFetch(status: number, body: unknown): jest.Mock {
  const mock = jest.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(body),
  } as Response);
  global.fetch = mock as unknown as typeof fetch;
  return mock;
}

describe("analyzeStock", () => {
  afterEach(() => {
    jest.resetAllMocks();
  });

  it("returns parsed JSON on 200", async () => {
    mockFetch(200, mockResponse);
    const result = await analyzeStock(mockRequest);
    expect(result).toEqual(mockResponse);
  });

  it("throws with ticker name and 'not found' on 404", async () => {
    mockFetch(404, {});
    await expect(analyzeStock(mockRequest)).rejects.toThrow(/AAPL/);
  });

  it("throws rate limit message on 429", async () => {
    mockFetch(429, {});
    await expect(analyzeStock(mockRequest)).rejects.toThrow(/rate limit/i);
  });

  it("throws service unavailable message on 500", async () => {
    mockFetch(500, {});
    await expect(analyzeStock(mockRequest)).rejects.toThrow(/unavailable/i);
  });

  it("throws network error message when fetch throws", async () => {
    global.fetch = jest
      .fn()
      .mockRejectedValue(new TypeError("Failed to fetch")) as unknown as typeof fetch;
    await expect(analyzeStock(mockRequest)).rejects.toThrow(/Unable to connect/i);
  });
});
