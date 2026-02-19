"use client";

import {
  LineChart,
  Line,
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

interface TooltipPayload {
  value: number;
  payload: PricePoint;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: TooltipPayload[];
}

function CustomTooltip({ active, payload }: CustomTooltipProps) {
  if (!active || !payload || payload.length === 0) return null;
  const { value, payload: point } = payload[0];
  return (
    <div className="rounded-lg border bg-background shadow-md px-3 py-2 text-sm">
      <p className="text-muted-foreground">{formatTooltipDate(point.date)}</p>
      <p className="font-semibold">{formatPrice(value)}</p>
    </div>
  );
}

export function PriceChart({ history }: PriceChartProps) {
  if (history.length === 0) return null;

  // Show every ~5th label to avoid crowding
  const tickInterval = Math.max(1, Math.floor(history.length / 5));

  // Compute y-axis domain with a small padding
  const closes = history.map((p) => p.close);
  const minClose = Math.min(...closes);
  const maxClose = Math.max(...closes);
  const padding = (maxClose - minClose) * 0.05 || 1;
  const yMin = Math.floor(minClose - padding);
  const yMax = Math.ceil(maxClose + padding);

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base">30-Day Price</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart
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
            <Tooltip content={<CustomTooltip />} />
            <Line
              type="monotone"
              dataKey="close"
              stroke="hsl(var(--primary))"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
