import { useMutation } from "@tanstack/react-query";
import { analyzeStock } from "@/lib/api";
import type { AnalyzeRequest, AnalyzeResponse } from "@/types";

export function useAnalysis() {
  return useMutation<AnalyzeResponse, Error, AnalyzeRequest>({
    mutationFn: analyzeStock,
  });
}
