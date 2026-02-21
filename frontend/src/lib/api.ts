import type { AnalyzeRequest, AnalyzeResponse } from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function analyzeStock(
  request: AnalyzeRequest
): Promise<AnalyzeResponse> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}/api/v1/analyze`, {
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
      throw new Error(
        `Ticker "${request.ticker}" not found. Verify the symbol and try again.`
      );
    }
    if (res.status === 429) {
      throw new Error(
        "Rate limit exceeded. Please wait a moment and try again."
      );
    }
    const body = await res.json().catch(() => ({}));
    throw new Error(
      body.detail ||
        (res.status >= 500
          ? "The analysis service is temporarily unavailable. Please try again shortly."
          : "Analysis failed.")
    );
  }

  return res.json();
}
