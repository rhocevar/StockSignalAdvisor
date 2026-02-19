import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
  if (signal === "bullish") return "bg-green-100 text-green-800 border-green-200";
  if (signal === "bearish") return "bg-red-100 text-red-800 border-red-200";
  return "bg-gray-100 text-gray-700 border-gray-200";
}

function trendBadgeVariant(trend: TrendDirection): string {
  return trend === "above"
    ? "bg-green-100 text-green-800 border-green-200"
    : "bg-red-100 text-red-800 border-red-200";
}

function volumeBadgeVariant(trend: VolumeTrend): string {
  if (trend === "high") return "bg-green-100 text-green-800 border-green-200";
  if (trend === "low") return "bg-amber-100 text-amber-800 border-amber-200";
  return "bg-gray-100 text-gray-700 border-gray-200";
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
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">Technical Analysis</CardTitle>
          {scorePct !== null && (
            <span className="text-sm text-muted-foreground">({scorePct}%)</span>
          )}
        </div>
        {score !== null && <ScoreBar score={score} />}
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-x-6 gap-y-3">
          {data.rsi !== null && (
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">RSI</span>
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
              <span className="text-sm text-muted-foreground">MACD</span>
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
              <span className="text-sm text-muted-foreground">vs SMA 50</span>
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
              <span className="text-sm text-muted-foreground">vs SMA 200</span>
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
              <span className="text-sm text-muted-foreground">Volume</span>
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
