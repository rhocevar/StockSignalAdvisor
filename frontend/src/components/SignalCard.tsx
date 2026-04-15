"use client";

import { useState } from "react";
import { Copy, Check } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { SignalBadge } from "@/components/SignalBadge";
import { InfoTooltip } from "@/components/InfoTooltip";
import { cn } from "@/lib/utils";
import type { PriceData, SignalType } from "@/types";

const SIGNAL_TOOLTIPS: Record<string, string> = {
  STRONG_BUY:  "Overwhelming bullish conviction across technical, fundamental, and sentiment pillars. Highest confidence in upward movement.",
  BUY:         "Clear bullish signals across most pillars. Good risk/reward for entering or adding to a position.",
  HOLD:        "Mixed or insufficient signals. Neither a compelling buy nor a sell — maintain current position and monitor.",
  SELL:        "Clear bearish signals across most pillars. Consider reducing exposure.",
  STRONG_SELL: "Overwhelming bearish conviction. Deteriorating fundamentals, poor technicals, and negative sentiment all align.",
};

interface SignalCardProps {
  ticker: string;
  companyName: string | null;
  signal: SignalType;
  confidence: number;
  priceData: PriceData | null;
}

function formatPrice(value: number | null, currency: string): string {
  if (value === null) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: currency || "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

function formatChange(value: number | null): string {
  if (value === null) return "—";
  const sign = value >= 0 ? "+" : "";
  return `${sign}${value.toFixed(2)}%`;
}

export function SignalCard({
  ticker,
  companyName,
  signal,
  confidence,
  priceData,
}: SignalCardProps) {
  const [copied, setCopied] = useState(false);
  const change1d = priceData?.change_percent_1d ?? null;
  const isPositiveChange = change1d !== null && change1d >= 0;

  function handleShare() {
    navigator.clipboard.writeText(window.location.href);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-2xl font-bold">{ticker}</CardTitle>
            {companyName && (
              <p className="text-sm text-muted-foreground mt-1">{companyName}</p>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={handleShare}
              title={copied ? "Copied!" : "Copy link"}
              className="h-7 w-7"
            >
              {copied ? (
                <Check className="h-3.5 w-3.5" />
              ) : (
                <Copy className="h-3.5 w-3.5" />
              )}
            </Button>
            <div className="flex items-center gap-1">
              <SignalBadge signal={signal} />
              <InfoTooltip content={SIGNAL_TOOLTIPS[signal] ?? "AI-generated trading signal based on technical, fundamental, and sentiment analysis."} />
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-3 sm:gap-6">
          {/* Confidence */}
          <div className="shrink-0">
            <p className="text-xs text-muted-foreground uppercase tracking-wide whitespace-nowrap">
              Confidence
              <InfoTooltip content="How strongly the AI's conviction aligns with this signal. Combines agreement across the technical, fundamental, and sentiment pillars — higher means more consistent evidence." />
            </p>
            <p className="text-xl sm:text-2xl font-semibold">
              {(confidence * 100).toFixed(1)}%
            </p>
          </div>

          {priceData && (
            <>
              <div className="h-10 w-px bg-border shrink-0" />

              {/* Current price */}
              <div className="min-w-0">
                <p className="text-xs text-muted-foreground uppercase tracking-wide whitespace-nowrap">
                  Price
                </p>
                <p className="text-xl sm:text-2xl font-semibold tabular-nums">
                  {formatPrice(priceData.current, priceData.currency)}
                </p>
              </div>

              {/* 1d change */}
              <div className="shrink-0">
                <p className="text-xs text-muted-foreground uppercase tracking-wide whitespace-nowrap">
                  1D Change
                </p>
                <p
                  className={cn(
                    "text-base sm:text-lg font-medium tabular-nums",
                    change1d === null
                      ? "text-muted-foreground"
                      : isPositiveChange
                        ? "text-green-600"
                        : "text-red-600"
                  )}
                >
                  {formatChange(change1d)}
                </p>
              </div>
            </>
          )}
        </div>

        {/* 52-week range */}
        {priceData && (priceData.high_52w !== null || priceData.low_52w !== null) && (
          <div className="pt-2 border-t">
            <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">
              52W Range
            </p>
            <p className="text-sm font-medium text-muted-foreground">
              {formatPrice(priceData.low_52w, priceData.currency)}
              <span className="mx-1 text-muted-foreground/60">—</span>
              {formatPrice(priceData.high_52w, priceData.currency)}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
