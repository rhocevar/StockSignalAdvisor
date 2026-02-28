"use client";

import { useState } from "react";
import { Copy, Check } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { SignalBadge } from "@/components/SignalBadge";
import { cn } from "@/lib/utils";
import type { PriceData, SignalType } from "@/types";

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
            <SignalBadge signal={signal} />
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-6">
          {/* Confidence */}
          <div>
            <p className="text-xs text-muted-foreground uppercase tracking-wide">
              Confidence
            </p>
            <p className="text-2xl font-semibold">
              {(confidence * 100).toFixed(1)}%
            </p>
          </div>

          {priceData && (
            <>
              <div className="h-10 w-px bg-border" />

              {/* Current price */}
              <div>
                <p className="text-xs text-muted-foreground uppercase tracking-wide">
                  Price
                </p>
                <p className="text-2xl font-semibold">
                  {formatPrice(priceData.current, priceData.currency)}
                </p>
              </div>

              {/* 1d change */}
              <div>
                <p className="text-xs text-muted-foreground uppercase tracking-wide">
                  1D Change
                </p>
                <p
                  className={cn(
                    "text-lg font-medium",
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
