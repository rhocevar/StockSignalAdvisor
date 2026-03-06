import { useState, useEffect, useCallback } from "react";
import { streamAnalysis } from "@/lib/api";
import type {
  TechnicalAnalysis,
  FundamentalAnalysis,
  SentimentAnalysis,
  NewsSource,
  AnalyzeResponse,
} from "@/types";

export type SentimentData = {
  analysis: SentimentAnalysis;
  sources: NewsSource[];
};

export type StreamingState = {
  technical: TechnicalAnalysis | null;
  fundamental: FundamentalAnalysis | null;
  sentimentData: SentimentData | null;
  result: AnalyzeResponse | null;
  isStreaming: boolean;
  error: string | null;
  restart: () => void;
};

export function useStreamingAnalysis(ticker: string): StreamingState {
  const [technical, setTechnical] = useState<TechnicalAnalysis | null>(null);
  const [fundamental, setFundamental] = useState<FundamentalAnalysis | null>(null);
  const [sentimentData, setSentimentData] = useState<SentimentData | null>(null);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [isStreaming, setIsStreaming] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);

  const restart = useCallback(() => {
    setTechnical(null);
    setFundamental(null);
    setSentimentData(null);
    setResult(null);
    setError(null);
    setIsStreaming(true);
    setAttempt((n) => n + 1);
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    streamAnalysis(
      ticker,
      (event) => {
        if (event.type === "technical") {
          setTechnical(event.data as TechnicalAnalysis);
        } else if (event.type === "fundamental") {
          setFundamental(event.data as FundamentalAnalysis);
        } else if (event.type === "sentiment") {
          setSentimentData(event.data as SentimentData);
        } else if (event.type === "complete") {
          const response = event.data as AnalyzeResponse;
          // Backfill pillar states from the complete event in case individual pillar
          // events were never emitted (cached results emit only a single complete event).
          if (response.analysis?.technical) setTechnical(response.analysis.technical);
          if (response.analysis?.fundamentals) setFundamental(response.analysis.fundamentals);
          if (response.analysis?.sentiment) {
            setSentimentData({
              analysis: response.analysis.sentiment,
              sources: response.sources ?? [],
            });
          }
          setResult(response);
          setIsStreaming(false);
        } else if (event.type === "error") {
          const errData = event.data as { code: number; message: string };
          setError(errData.message);
          setIsStreaming(false);
        }
      },
      controller.signal,
    ).catch((err: Error) => {
      if (err.name !== "AbortError") {
        setError(err.message ?? "Analysis service temporarily unavailable.");
        setIsStreaming(false);
      }
    });

    return () => controller.abort();
  }, [ticker, attempt]);

  return { technical, fundamental, sentimentData, result, isStreaming, error, restart };
}
