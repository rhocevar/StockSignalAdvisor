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

interface AnalysisViewProps {
  ticker: string;
}

export function AnalysisView({ ticker }: AnalysisViewProps) {
  const { mutate, isPending, data, error } = useAnalysis();

  // useMutation state is not persisted between component mounts, so we must
  // allow mutate to fire on every mount. React StrictMode double-invokes this
  // effect in development, causing two requests — but the backend TTL cache
  // absorbs the duplicate immediately, making it harmless.
  useEffect(() => {
    mutate({ ticker });
  }, [ticker, mutate]);

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
            onClick={() => mutate({ ticker })}
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
    </div>
  );
}
