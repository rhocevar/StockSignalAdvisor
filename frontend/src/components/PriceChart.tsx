"use client";

import {
  ComposedChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { PricePoint } from "@/types";

interface PriceChartProps {
  history: PricePoint[];
}

function formatAxisDate(dateStr: string): string {
  const date = new Date(dateStr + "T00:00:00");
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
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
  if (history.length === 0) return null;

  // Show every ~5th label to avoid crowding
  const tickInterval = Math.max(1, Math.floor(history.length / 5));

  // Y-axis domain spans full high/low range with small padding
  const allHighs = history.map((p) => p.high);
  const allLows = history.map((p) => p.low);
  const rangeHigh = Math.max(...allHighs);
  const rangeLow = Math.min(...allLows);
  const padding = (rangeHigh - rangeLow) * 0.05 || 1;
  const yMin = Math.floor(rangeLow - padding);
  const yMax = Math.ceil(rangeHigh + padding);

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base">30-Day Price</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={200}>
          <ComposedChart
            data={history}
            margin={{ top: 4, right: 8, bottom: 0, left: 8 }}
          >
            <XAxis
              dataKey="date"
              tickFormatter={formatAxisDate}
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
