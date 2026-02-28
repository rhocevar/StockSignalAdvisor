"use client";

import { useEffect } from "react";
import { useAnalysis } from "@/hooks/useAnalysis";
import { LoadingState } from "@/components/LoadingState";
import { SignalCard } from "@/components/SignalCard";
import { PriceChart } from "@/components/PriceChart";
import { ExplanationPanel } from "@/components/ExplanationPanel";
import { TechnicalIndicators } from "@/components/TechnicalIndicators";
import { FundamentalsCard } from "@/components/FundamentalsCard";
import { SourcesList } from "@/components/SourcesList";
import { Disclaimer } from "@/components/Disclaimer";
import { Button } from "@/components/ui/button";
import { saveRecentTicker } from "@/components/RecentSearches";

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
  const { isPending, data, error, refetch } = useAnalysis(ticker);

  useEffect(() => {
    if (data) saveRecentTicker(ticker);
  }, [data, ticker]);

  if (isPending) {
    return <LoadingState />;
  }

  if (error) {
    return (
      <div className="w-full max-w-2xl mx-auto p-8">
        <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-center space-y-4">
          <p className="text-sm font-medium text-red-700">
            Analysis failed for{" "}
            <span className="font-mono font-bold">{ticker}</span>
          </p>
          <p className="text-xs text-red-600">{error.message}</p>
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
          >
            Try Again
          </Button>
        </div>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  const priceHistory = data.price_data?.price_history ?? [];

  return (
    <div className="w-full max-w-2xl mx-auto p-8 space-y-4">
      <SignalCard
        ticker={data.ticker}
        companyName={data.company_name}
        signal={data.signal}
        confidence={data.confidence}
        priceData={data.price_data}
      />
      {priceHistory.length > 0 && <PriceChart history={priceHistory} />}
      <ExplanationPanel explanation={data.explanation} />
      {data.analysis.technical && (
        <TechnicalIndicators data={data.analysis.technical} />
      )}
      {data.analysis.fundamentals && (
        <FundamentalsCard data={data.analysis.fundamentals} />
      )}
      <SourcesList sources={data.sources} />
      <Disclaimer />
      <div className="text-xs text-muted-foreground text-center space-y-0.5 mt-2 pb-2">
        <p>
          {data.metadata.model_used} · {data.metadata.llm_provider} · {data.metadata.vectorstore_provider}
        </p>
        <p>
          <span
            className={`inline-block w-1.5 h-1.5 rounded-full mr-1.5 align-middle ${
              data.metadata.cached ? "bg-amber-400" : "bg-green-500"
            }`}
          />
          {data.metadata.cached ? "Cached result" : "Live analysis"}
          {" · "}Generated {formatRelativeTime(data.metadata.generated_at)}
        </p>
      </div>
    </div>
  );
}
