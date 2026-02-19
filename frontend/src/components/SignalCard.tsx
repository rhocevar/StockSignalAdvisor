import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
  const change1d = priceData?.change_percent_1d ?? null;
  const isPositiveChange = change1d !== null && change1d >= 0;

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
          <SignalBadge signal={signal} />
        </div>
      </CardHeader>
      <CardContent>
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
      </CardContent>
    </Card>
  );
}
