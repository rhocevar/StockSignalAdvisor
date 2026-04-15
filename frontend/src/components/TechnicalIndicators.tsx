import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { InfoTooltip } from "@/components/InfoTooltip";
import { cn } from "@/lib/utils";
import type { TechnicalAnalysis, MacdSignal, TrendDirection, VolumeTrend } from "@/types";

interface TechnicalIndicatorsProps {
  data: TechnicalAnalysis;
}

function ScoreBar({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const color =
    pct >= 60 ? "bg-green-500" : pct >= 40 ? "bg-amber-500" : "bg-red-500";
  return (
    <div className="w-full bg-muted rounded-full h-2">
      <div
        className={cn("h-2 rounded-full transition-all", color)}
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}

function macdBadgeVariant(signal: MacdSignal): string {
  if (signal === "bullish") return "bg-green-100 text-green-800 border-green-200 dark:bg-green-900/40 dark:text-green-300 dark:border-green-700";
  if (signal === "bearish") return "bg-red-100 text-red-800 border-red-200 dark:bg-red-900/40 dark:text-red-300 dark:border-red-700";
  return "bg-gray-100 text-gray-700 border-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-700";
}

function trendBadgeVariant(trend: TrendDirection): string {
  return trend === "above"
    ? "bg-green-100 text-green-800 border-green-200 dark:bg-green-900/40 dark:text-green-300 dark:border-green-700"
    : "bg-red-100 text-red-800 border-red-200 dark:bg-red-900/40 dark:text-red-300 dark:border-red-700";
}

function volumeBadgeVariant(trend: VolumeTrend): string {
  if (trend === "high") return "bg-green-100 text-green-800 border-green-200 dark:bg-green-900/40 dark:text-green-300 dark:border-green-700";
  if (trend === "low") return "bg-amber-100 text-amber-800 border-amber-200 dark:bg-amber-900/40 dark:text-amber-300 dark:border-amber-700";
  return "bg-gray-100 text-gray-700 border-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-700";
}

function rsiColor(rsi: number): string {
  if (rsi >= 70) return "text-red-600";
  if (rsi <= 30) return "text-green-600";
  return "text-foreground";
}

export function TechnicalIndicators({ data }: TechnicalIndicatorsProps) {
  const score = data.technical_score;
  const scorePct = score !== null ? Math.round(score * 100) : null;

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between gap-2">
          <CardTitle className="text-base min-w-0 truncate">Technical Analysis</CardTitle>
          {scorePct !== null && (
            <span className="text-sm text-muted-foreground shrink-0 flex items-center">
              Bullishness Score ({scorePct}%)
              <InfoTooltip content="Composite 0–100% score of technical momentum. ≥60% is bullish, ≤40% is bearish. Derived from RSI, MACD, moving averages, and volume." />
            </span>
          )}
        </div>
        {score !== null && <ScoreBar score={score} />}
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-x-4 sm:gap-x-6 gap-y-3">
          {data.rsi !== null && (
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground flex items-center">
                RSI
                <InfoTooltip content="Relative Strength Index (14-day). Below 30 = oversold (bullish signal). Above 70 = overbought (bearish signal). 30–70 = neutral." />
              </span>
              <span className={cn("text-sm font-medium", rsiColor(data.rsi))}>
                {data.rsi.toFixed(1)}
                {data.rsi_interpretation && (
                  <span className="ml-1 text-xs text-muted-foreground">
                    ({data.rsi_interpretation})
                  </span>
                )}
              </span>
            </div>
          )}

          {data.macd_signal !== null && (
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground flex items-center">
                MACD
                <InfoTooltip content="Moving Average Convergence Divergence. Bullish when the MACD line crosses above its signal line, indicating upward momentum." />
              </span>
              <span
                className={cn(
                  "inline-flex items-center rounded border px-2 py-0.5 text-xs font-medium",
                  macdBadgeVariant(data.macd_signal)
                )}
              >
                {data.macd_signal}
              </span>
            </div>
          )}

          {data.price_vs_sma50 !== null && (
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground flex items-center">
                vs SMA 50
                <InfoTooltip content="Price position relative to the 50-day Simple Moving Average. Trading above is a short-term bullish signal." />
              </span>
              <span
                className={cn(
                  "inline-flex items-center rounded border px-2 py-0.5 text-xs font-medium",
                  trendBadgeVariant(data.price_vs_sma50)
                )}
              >
                {data.price_vs_sma50}
              </span>
            </div>
          )}

          {data.price_vs_sma200 !== null && (
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground flex items-center">
                vs SMA 200
                <InfoTooltip content="Price position relative to the 200-day Simple Moving Average. Trading above is a long-term bullish signal." />
              </span>
              <span
                className={cn(
                  "inline-flex items-center rounded border px-2 py-0.5 text-xs font-medium",
                  trendBadgeVariant(data.price_vs_sma200)
                )}
              >
                {data.price_vs_sma200}
              </span>
            </div>
          )}

          {data.volume_trend !== null && (
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground flex items-center">
                Volume
                <InfoTooltip content="Recent trading volume relative to the 20-day average. High volume confirms price moves; low volume suggests weak conviction." />
              </span>
              <span
                className={cn(
                  "inline-flex items-center rounded border px-2 py-0.5 text-xs font-medium",
                  volumeBadgeVariant(data.volume_trend)
                )}
              >
                {data.volume_trend}
              </span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
