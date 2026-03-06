import { analyzeStock, streamAnalysis, ApiError } from "@/lib/api";
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

function mockStreamFetch(body: string, status = 200): void {
  const bytes = new Uint8Array(Buffer.from(body, "utf-8"));
  let consumed = false;
  const mockReader = {
    read: jest.fn().mockImplementation(() => {
      if (!consumed) {
        consumed = true;
        return Promise.resolve({ done: false, value: bytes });
      }
      return Promise.resolve({ done: true, value: undefined });
    }),
    releaseLock: jest.fn(),
  };
  global.fetch = jest.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    body: { getReader: () => mockReader },
  } as unknown as Response);
}

describe("streamAnalysis", () => {
  afterEach(() => {
    jest.resetAllMocks();
  });

  it("calls onEvent for each SSE data line", async () => {
    const body =
      'data: {"type":"technical","data":{"score":0.7}}\n\n' +
      'data: {"type":"complete","data":{"ticker":"AAPL"}}\n\n';
    mockStreamFetch(body);

    const onEvent = jest.fn();
    await streamAnalysis("AAPL", onEvent);

    expect(onEvent).toHaveBeenCalledTimes(2);
    expect(onEvent).toHaveBeenNthCalledWith(1, { type: "technical", data: { score: 0.7 } });
    expect(onEvent).toHaveBeenNthCalledWith(2, { type: "complete", data: { ticker: "AAPL" } });
  });

  it("ignores non-data lines (comments and blanks)", async () => {
    const body =
      ": this is a comment\n\n" +
      'data: {"type":"complete","data":{}}\n\n';
    mockStreamFetch(body);

    const onEvent = jest.fn();
    await streamAnalysis("AAPL", onEvent);

    expect(onEvent).toHaveBeenCalledTimes(1);
    expect(onEvent).toHaveBeenCalledWith({ type: "complete", data: {} });
  });

  it("rejects with AbortError when signal is already aborted", async () => {
    const abortError = Object.assign(new Error("The user aborted a request."), {
      name: "AbortError",
    });
    global.fetch = jest.fn().mockRejectedValue(abortError) as unknown as typeof fetch;

    const onEvent = jest.fn();
    const controller = new AbortController();
    controller.abort();

    await expect(streamAnalysis("AAPL", onEvent, controller.signal)).rejects.toMatchObject({
      name: "AbortError",
    });
    expect(onEvent).not.toHaveBeenCalled();
  });
});

describe("analyzeStock", () => {
  afterEach(() => {
    jest.resetAllMocks();
  });

  it("returns parsed JSON on 200", async () => {
    mockFetch(200, mockResponse);
    const result = await analyzeStock(mockRequest);
    expect(result).toEqual(mockResponse);
  });

  it("throws ApiError with status 404 and ticker name on 404", async () => {
    mockFetch(404, {});
    const error = await analyzeStock(mockRequest).catch((e) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).status).toBe(404);
    expect(error.message).toMatch(/AAPL/);
  });

  it("throws ApiError with status 429 on rate limit", async () => {
    mockFetch(429, {});
    const error = await analyzeStock(mockRequest).catch((e) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).status).toBe(429);
    expect(error.message).toMatch(/rate limit/i);
  });

  it("throws ApiError with status 500 on server error", async () => {
    mockFetch(500, {});
    const error = await analyzeStock(mockRequest).catch((e) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).status).toBe(500);
    expect(error.message).toMatch(/unavailable/i);
  });

  it("throws network error message when fetch throws", async () => {
    global.fetch = jest
      .fn()
      .mockRejectedValue(new TypeError("Failed to fetch")) as unknown as typeof fetch;
    await expect(analyzeStock(mockRequest)).rejects.toThrow(/Unable to connect/i);
  });
});
