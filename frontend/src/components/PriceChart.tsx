"use client";

import { useState } from "react";
import {
  ComposedChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { PricePoint } from "@/types";

const PERIOD_CONFIG = [
  { period: "30D", days: 30,   aggregate: "daily"   },
  { period: "90D", days: 90,   aggregate: "daily"   },
  { period: "6M",  days: 182,  aggregate: "weekly"  },
  { period: "1Y",  days: 365,  aggregate: "weekly"  },
  { period: "2Y",  days: 730,  aggregate: "monthly" },
  { period: "5Y",  days: 1825, aggregate: "monthly" },
] as const;

type Period = (typeof PERIOD_CONFIG)[number]["period"];

/** Return the ISO year-week key for a date string "YYYY-MM-DD" */
function isoWeekKey(dateStr: string): string {
  const d = new Date(dateStr + "T12:00:00");
  const thu = new Date(d);
  thu.setDate(d.getDate() - ((d.getDay() + 6) % 7) + 3);
  const yearStart = new Date(thu.getFullYear(), 0, 1);
  const week = Math.ceil(((thu.getTime() - yearStart.getTime()) / 86400000 + 1) / 7);
  return `${thu.getFullYear()}-W${String(week).padStart(2, "0")}`;
}

/** Return the "YYYY-MM" key for a date string */
function monthKey(dateStr: string): string {
  return dateStr.slice(0, 7);
}

/** Aggregate an ordered array of daily candles into weekly or monthly candles. */
function aggregateCandles(candles: PricePoint[], mode: "weekly" | "monthly"): PricePoint[] {
  const buckets = new Map<string, PricePoint[]>();
  for (const c of candles) {
    const key = mode === "weekly" ? isoWeekKey(c.date) : monthKey(c.date);
    if (!buckets.has(key)) buckets.set(key, []);
    buckets.get(key)!.push(c);
  }
  const result: PricePoint[] = [];
  buckets.forEach((group) => {
    result.push({
      date:  group[0].date,
      open:  group[0].open,
      close: group[group.length - 1].close,
      high:  Math.max(...group.map((g) => g.high)),
      low:   Math.min(...group.map((g) => g.low)),
    });
  });
  return result;
}

type PeriodConfig = (typeof PERIOD_CONFIG)[number];

/** Slice history to the most recent `days` calendar days and optionally aggregate. */
function sliceHistory(history: PricePoint[], config: PeriodConfig): PricePoint[] {
  const cutoff = new Date();
  cutoff.setDate(cutoff.getDate() - config.days);
  const cutoffStr = cutoff.toISOString().slice(0, 10);
  const sliced = history.filter((p) => p.date >= cutoffStr);
  if (config.aggregate !== "daily") {
    return aggregateCandles(sliced, config.aggregate);
  }
  return sliced;
}

interface PriceChartProps {
  history: PricePoint[];
}

function makeAxisTickFormatter(candles: PricePoint[]) {
  const years = new Set(candles.map((c) => c.date.slice(0, 4)));
  const multiYear = years.size > 1;
  return (dateStr: string) => {
    const date = new Date(dateStr + "T00:00:00");
    if (multiYear) {
      return date.toLocaleDateString("en-US", { month: "short", year: "2-digit" });
    }
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  };
}

function formatTooltipDate(dateStr: string): string {
  const date = new Date(dateStr + "T00:00:00");
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function formatPrice(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

// Custom candlestick shape rendered inside a Bar whose dataKey spans [low, high].
// Recharts sets y = pixel top (= high) and y+height = pixel bottom (= low),
// so we can project open/close into that coordinate space to draw the body.
function CandlestickShape(props: {
  x?: number;
  y?: number;
  width?: number;
  height?: number;
  payload?: PricePoint;
}) {
  const { x = 0, y = 0, width = 0, height = 0, payload } = props;
  if (!payload || height <= 0) return null;

  const { open, close, high, low } = payload;
  const range = high - low;
  if (range === 0) return null;

  const isUp = close >= open;
  const color = isUp ? "#22c55e" : "#ef4444";
  const centerX = x + width / 2;

  // Map a data value to a pixel Y within the bar's bounding box
  const toPixelY = (v: number) => y + ((high - v) / range) * height;

  const openY = toPixelY(open);
  const closeY = toPixelY(close);
  const bodyTop = Math.min(openY, closeY);
  const bodyHeight = Math.max(1, Math.abs(openY - closeY));
  const bodyWidth = Math.max(2, width * 0.7);

  return (
    <g>
      {/* Full wick: high to low */}
      <line x1={centerX} y1={y} x2={centerX} y2={y + height} stroke={color} strokeWidth={1} />
      {/* Candle body: open to close */}
      <rect
        x={centerX - bodyWidth / 2}
        y={bodyTop}
        width={bodyWidth}
        height={bodyHeight}
        fill={color}
        stroke={color}
        strokeWidth={0.5}
      />
    </g>
  );
}

interface TooltipPayload {
  payload: PricePoint;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: TooltipPayload[];
}

function CustomTooltip({ active, payload }: CustomTooltipProps) {
  if (!active || !payload || payload.length === 0) return null;
  const point = payload[0].payload;
  const isUp = point.close >= point.open;
  return (
    <div className="rounded-lg border bg-background shadow-md px-3 py-2 text-sm">
      <p className="text-muted-foreground mb-1">{formatTooltipDate(point.date)}</p>
      <div className="grid grid-cols-2 gap-x-3 text-xs">
        <span className="text-muted-foreground">O</span><span>{formatPrice(point.open)}</span>
        <span className="text-muted-foreground">H</span><span>{formatPrice(point.high)}</span>
        <span className="text-muted-foreground">L</span><span>{formatPrice(point.low)}</span>
        <span className="text-muted-foreground">C</span>
        <span className={`font-semibold ${isUp ? "text-green-500" : "text-red-500"}`}>
          {formatPrice(point.close)}
        </span>
      </div>
    </div>
  );
}

export function PriceChart({ history }: PriceChartProps) {
  const [period, setPeriod] = useState<Period>("30D");

  if (history.length === 0) return null;

  const config = PERIOD_CONFIG.find((c) => c.period === period)!;
  const candles = sliceHistory(history, config);

  // Show every ~5th label to avoid crowding
  const tickInterval = Math.max(1, Math.floor(candles.length / 5));

  // Y-axis domain spans full high/low range with small padding
  const allHighs = candles.map((p) => p.high);
  const allLows = candles.map((p) => p.low);
  const rangeHigh = Math.max(...allHighs);
  const rangeLow = Math.min(...allLows);
  const padding = (rangeHigh - rangeLow) * 0.05 || 1;
  const yMin = Math.floor(rangeLow - padding);
  const yMax = Math.ceil(rangeHigh + padding);

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">Price History</CardTitle>
          <div className="flex gap-1">
            {PERIOD_CONFIG.map(({ period: p }) => (
              <button
                key={p}
                onClick={() => setPeriod(p)}
                className={`px-2 py-0.5 text-xs rounded font-medium transition-colors ${
                  period === p
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted"
                }`}
              >
                {p}
              </button>
            ))}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={240}>
          <ComposedChart
            data={candles}
            margin={{ top: 4, right: 8, bottom: 0, left: 8 }}
          >
            <CartesianGrid vertical={false} stroke="hsl(var(--border))" strokeOpacity={0.5} />
            <XAxis
              dataKey="date"
              tickFormatter={makeAxisTickFormatter(candles)}
              interval={tickInterval}
              tick={{ fontSize: 11 }}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              domain={[yMin, yMax]}
              tickFormatter={(v: number) => `$${v.toFixed(0)}`}
              tick={{ fontSize: 11 }}
              tickLine={false}
              axisLine={false}
              width={48}
            />
            <Tooltip
              content={<CustomTooltip />}
              cursor={{ fill: "hsl(var(--muted))", opacity: 0.3 }}
            />
            <Bar
              dataKey={(d: PricePoint) => [d.low, d.high]}
              shape={(props: object) => (
                <CandlestickShape {...(props as Parameters<typeof CandlestickShape>[0])} />
              )}
              isAnimationActive={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
