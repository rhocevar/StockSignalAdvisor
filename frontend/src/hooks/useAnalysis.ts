import { useQuery } from "@tanstack/react-query";
import { analyzeStock } from "@/lib/api";
import type { AnalyzeResponse } from "@/types";

export function useAnalysis(ticker: string) {
  return useQuery<AnalyzeResponse, Error>({
    queryKey: ["analysis", ticker],
    queryFn: () => analyzeStock({ ticker }),
    staleTime: 60 * 60 * 1000, // 1 hour — matches backend TTL cache
    enabled: ticker.length > 0,
  });
}
