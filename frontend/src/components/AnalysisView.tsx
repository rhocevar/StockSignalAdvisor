"use client";

import { useEffect, useState } from "react";
import { LoaderCircle } from "lucide-react";
import { useStreamingAnalysis } from "@/hooks/useStreamingAnalysis";
import { SignalCard } from "@/components/SignalCard";
import { PriceChart } from "@/components/PriceChart";
import { ExplanationPanel } from "@/components/ExplanationPanel";
import { TechnicalIndicators } from "@/components/TechnicalIndicators";
import { FundamentalsCard } from "@/components/FundamentalsCard";
import { SourcesList } from "@/components/SourcesList";
import { Disclaimer } from "@/components/Disclaimer";
import { Button } from "@/components/ui/button";
import { saveRecentTicker } from "@/components/RecentSearches";

const STATUS_STEPS = [
  "Fetching market data...",
  "Calculating technical indicators...",
  "Evaluating fundamentals...",
  "Analyzing news sentiment...",
  "Running AI analysis...",
  "Assembling recommendation...",
];

function AnalysisProgressHeader() {
  const [stepIndex, setStepIndex] = useState(0);
  useEffect(() => {
    const interval = setInterval(
      () => setStepIndex((i) => (i + 1) % STATUS_STEPS.length),
      2500,
    );
    return () => clearInterval(interval);
  }, []);
  return (
    <div className="flex flex-col items-center gap-2 py-2">
      <LoaderCircle className="h-6 w-6 text-primary animate-spin" />
      <p className="text-sm font-medium text-foreground">{STATUS_STEPS[stepIndex]}</p>
      <p className="text-xs text-muted-foreground">AI analysis typically takes 10–20 seconds</p>
    </div>
  );
}

function SignalCardSkeleton() {
  return (
    <div className="rounded-xl border bg-card shadow p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <div className="h-5 w-32 bg-muted animate-pulse rounded" />
          <div className="h-4 w-20 bg-muted animate-pulse rounded" />
        </div>
        <div className="h-8 w-16 bg-muted animate-pulse rounded-md" />
      </div>
      <div className="flex items-center gap-4">
        <div className="h-8 w-24 bg-muted animate-pulse rounded" />
        <div className="h-6 w-16 bg-muted animate-pulse rounded" />
      </div>
      <div className="h-4 w-40 bg-muted animate-pulse rounded" />
    </div>
  );
}

function PriceChartSkeleton() {
  return (
    <div className="rounded-xl border bg-card shadow p-6 space-y-3">
      <div className="h-5 w-32 bg-muted animate-pulse rounded" />
      <div className="h-60 w-full bg-muted animate-pulse rounded-md" />
    </div>
  );
}

function ExplanationSkeleton() {
  return (
    <div className="rounded-xl border bg-card shadow p-6 space-y-3">
      <div className="h-5 w-28 bg-muted animate-pulse rounded" />
      <div className="space-y-2">
        <div className="h-4 w-full bg-muted animate-pulse rounded" />
        <div className="h-4 w-full bg-muted animate-pulse rounded" />
        <div className="h-4 w-3/4 bg-muted animate-pulse rounded" />
      </div>
    </div>
  );
}

function TechnicalSkeleton() {
  return (
    <div className="rounded-xl border bg-card shadow p-6 space-y-4">
      <div className="h-5 w-40 bg-muted animate-pulse rounded" />
      <div className="h-2 w-full bg-muted animate-pulse rounded-full" />
      <div className="grid grid-cols-2 gap-3">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="flex items-center justify-between">
            <div className="h-4 w-12 bg-muted animate-pulse rounded" />
            <div className="h-5 w-16 bg-muted animate-pulse rounded-md" />
          </div>
        ))}
      </div>
    </div>
  );
}

function FundamentalsSkeleton() {
  return (
    <div className="rounded-xl border bg-card shadow p-6 space-y-4">
      <div className="h-5 w-44 bg-muted animate-pulse rounded" />
      <div className="h-2 w-full bg-muted animate-pulse rounded-full" />
      <div className="grid grid-cols-2 gap-3">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div key={i} className="flex items-center justify-between">
            <div className="h-4 w-20 bg-muted animate-pulse rounded" />
            <div className="h-4 w-14 bg-muted animate-pulse rounded" />
          </div>
        ))}
      </div>
    </div>
  );
}

function SourcesSkeleton() {
  return (
    <div className="rounded-xl border bg-card shadow p-6 space-y-3">
      <div className="h-5 w-24 bg-muted animate-pulse rounded" />
      {[1, 2, 3].map((i) => (
        <div key={i} className="flex items-center justify-between py-2 border-b last:border-0">
          <div className="space-y-1.5">
            <div className="h-4 w-48 bg-muted animate-pulse rounded" />
            <div className="h-3 w-24 bg-muted animate-pulse rounded" />
          </div>
          <div className="h-5 w-14 bg-muted animate-pulse rounded-md" />
        </div>
      ))}
    </div>
  );
}

function formatRelativeTime(isoString: string): string {
  const diffMin = Math.floor((Date.now() - new Date(isoString).getTime()) / 60_000);
  if (diffMin < 1) return "just now";
  if (diffMin < 60) return `${diffMin} min ago`;
  const diffHr = Math.floor(diffMin / 60);
  return diffHr === 1 ? "1 hour ago" : `${diffHr} hours ago`;
}

interface AnalysisViewProps {
  ticker: string;
}

export function AnalysisView({ ticker }: AnalysisViewProps) {
  const { technical, fundamental, sentimentData, result, isStreaming, error, restart } =
    useStreamingAnalysis(ticker);

  useEffect(() => {
    if (result) saveRecentTicker(ticker);
  }, [result, ticker]);

  if (error) {
    return (
      <div className="w-full max-w-2xl mx-auto p-8">
        <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-center space-y-4 dark:border-red-800 dark:bg-red-950/40">
          <p className="text-sm font-medium text-red-700 dark:text-red-400">
            Analysis failed for{" "}
            <span className="font-mono font-bold">{ticker}</span>
          </p>
          <p className="text-xs text-red-600 dark:text-red-400">{error}</p>
          <Button variant="outline" size="sm" onClick={restart}>
            Try Again
          </Button>
        </div>
      </div>
    );
  }

  // Not yet started (shouldn't normally be visible)
  if (!isStreaming && !result) {
    return null;
  }

  const priceHistory = result?.price_data?.price_history ?? [];

  return (
    <div className="w-full max-w-2xl mx-auto p-8 space-y-4">
      {/* Progress header — visible until the complete event arrives */}
      {isStreaming && <AnalysisProgressHeader />}

      {/* Signal / price / explanation — skeleton until complete event */}
      {result ? (
        <>
          <SignalCard
            ticker={result.ticker}
            companyName={result.company_name}
            signal={result.signal}
            confidence={result.confidence}
            priceData={result.price_data}
          />
          {priceHistory.length > 0 && <PriceChart history={priceHistory} />}
          <ExplanationPanel explanation={result.explanation} />
        </>
      ) : (
        <>
          <SignalCardSkeleton />
          <PriceChartSkeleton />
          <ExplanationSkeleton />
        </>
      )}

      {/* Technical — skeleton until technical event (or complete for cached) */}
      {technical ? (
        <TechnicalIndicators data={technical} />
      ) : isStreaming ? (
        <TechnicalSkeleton />
      ) : null}

      {/* Fundamentals — skeleton until fundamental event (or complete for cached) */}
      {fundamental ? (
        <FundamentalsCard data={fundamental} />
      ) : isStreaming ? (
        <FundamentalsSkeleton />
      ) : null}

      {/* News sources — skeleton until sentiment event (or complete for cached) */}
      {sentimentData ? (
        <SourcesList sources={sentimentData.sources} />
      ) : isStreaming ? (
        <SourcesSkeleton />
      ) : null}

      {result && <Disclaimer />}
      {result && (
        <div className="text-xs text-muted-foreground text-center space-y-0.5 mt-2 pb-2">
          <p>
            {result.metadata.model_used} · {result.metadata.llm_provider} · {result.metadata.vectorstore_provider}
          </p>
          <p>
            <span
              className={`inline-block w-1.5 h-1.5 rounded-full mr-1.5 align-middle ${
                result.metadata.cached ? "bg-amber-400" : "bg-green-500"
              }`}
            />
            {result.metadata.cached ? "Cached result" : "Live analysis"}
            {" · "}Generated {formatRelativeTime(result.metadata.generated_at)}
          </p>
        </div>
      )}
    </div>
  );
}
