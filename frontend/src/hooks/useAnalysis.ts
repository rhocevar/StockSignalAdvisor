import { useQuery } from "@tanstack/react-query";
import { analyzeStock, ApiError } from "@/lib/api";
import type { AnalyzeResponse } from "@/types";

export function useAnalysis(ticker: string) {
  return useQuery<AnalyzeResponse, Error>({
    queryKey: ["analysis", ticker],
    queryFn: () => analyzeStock({ ticker }),
    staleTime: 60 * 60 * 1000, // 1 hour — matches backend TTL cache
    enabled: ticker.length > 0,
    // Don't retry 4xx errors (bad ticker, rate limit) — only retry on 5xx/network failures.
    retry: (failureCount, error) =>
      !(error instanceof ApiError && error.status < 500) && failureCount < 2,
  });
}
