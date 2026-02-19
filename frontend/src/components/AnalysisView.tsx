"use client";

import { useEffect } from "react";
import { useAnalysis } from "@/hooks/useAnalysis";
import { LoadingState } from "@/components/LoadingState";
import { SignalCard } from "@/components/SignalCard";
import { ExplanationPanel } from "@/components/ExplanationPanel";
import { SourcesList } from "@/components/SourcesList";
import { Disclaimer } from "@/components/Disclaimer";
import { Button } from "@/components/ui/button";

interface AnalysisViewProps {
  ticker: string;
}

export function AnalysisView({ ticker }: AnalysisViewProps) {
  const { mutate, isPending, data, error } = useAnalysis();

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

  return (
    <div className="w-full max-w-2xl mx-auto p-8 space-y-4">
      <SignalCard
        ticker={data.ticker}
        companyName={data.company_name}
        signal={data.signal}
        confidence={data.confidence}
        priceData={data.price_data}
      />
      <ExplanationPanel explanation={data.explanation} />
      <SourcesList sources={data.sources} />
      <Disclaimer />
    </div>
  );
}
