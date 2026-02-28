import type { AnalyzeRequest, AnalyzeResponse } from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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
