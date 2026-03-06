import type { AnalyzeRequest, AnalyzeResponse } from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type SseEvent = {
  type: string;
  data: unknown;
};

export class ApiError extends Error {
  readonly status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export async function analyzeStock(
  request: AnalyzeRequest
): Promise<AnalyzeResponse> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}/api/v1/signal`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });
  } catch {
    throw new Error(
      "Unable to connect to the analysis service. Check your network connection."
    );
  }

  if (!res.ok) {
    if (res.status === 404) {
      throw new ApiError(
        `Ticker "${request.ticker}" not found. Verify the symbol and try again.`,
        404
      );
    }
    if (res.status === 429) {
      throw new ApiError(
        "Rate limit exceeded. Please wait a moment and try again.",
        429
      );
    }
    const body = await res.json().catch(() => ({}));
    throw new ApiError(
      body.detail ||
        (res.status >= 500
          ? "The analysis service is temporarily unavailable. Please try again shortly."
          : "Analysis failed."),
      res.status
    );
  }

  return res.json();
}

export async function streamAnalysis(
  ticker: string,
  onEvent: (event: SseEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch(
    `${API_BASE_URL}/api/v1/signal/stream?ticker=${encodeURIComponent(ticker)}`,
    { headers: { Accept: "text/event-stream" }, signal },
  );

  if (!res.ok || !res.body) {
    throw new ApiError("Stream request failed", res.status);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split("\n\n");
      buffer = parts.pop() ?? "";
      for (const part of parts) {
        for (const line of part.split("\n")) {
          if (line.startsWith("data: ")) {
            try {
              onEvent(JSON.parse(line.slice(6)) as SseEvent);
            } catch {
              // ignore malformed JSON lines
            }
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}
