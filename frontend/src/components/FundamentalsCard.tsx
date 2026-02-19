import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { FundamentalAnalysis } from "@/types";

interface FundamentalsCardProps {
  data: FundamentalAnalysis;
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

function pct(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

function ratio(value: number): string {
  return value.toFixed(2);
}

function formatCash(value: number): string {
  const abs = Math.abs(value);
  const sign = value < 0 ? "-" : "";
  if (abs >= 1e12) return `${sign}$${(abs / 1e12).toFixed(1)}T`;
  if (abs >= 1e9) return `${sign}$${(abs / 1e9).toFixed(1)}B`;
  if (abs >= 1e6) return `${sign}$${(abs / 1e6).toFixed(1)}M`;
  return `${sign}$${abs.toFixed(0)}`;
}

interface MetricRowProps {
  label: string;
  value: number | null;
  formatter: (v: number) => string;
}

function MetricRow({ label, value, formatter }: MetricRowProps) {
  if (value === null) return null;
  return (
    <div className="flex items-center justify-between py-0.5">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className="text-sm font-medium">{formatter(value)}</span>
    </div>
  );
}

interface SectionProps {
  title: string;
  children: React.ReactNode;
}

function Section({ title, children }: SectionProps) {
  return (
    <div>
      <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1">
        {title}
      </p>
      {children}
    </div>
  );
}

export function FundamentalsCard({ data }: FundamentalsCardProps) {
  const score = data.fundamental_score;
  const scorePct = score !== null ? Math.round(score * 100) : null;

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">Fundamental Analysis</CardTitle>
          {scorePct !== null && (
            <span className="text-sm text-muted-foreground">Bullishness Score ({scorePct}%)</span>
          )}
        </div>
        {score !== null && <ScoreBar score={score} />}
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Insights */}
        {data.insights.length > 0 && (
          <ul className="space-y-1">
            {data.insights.map((insight, i) => (
              <li key={i} className="text-sm text-muted-foreground flex gap-2">
                <span className="mt-1 shrink-0 h-1.5 w-1.5 rounded-full bg-muted-foreground/60" />
                {insight}
              </li>
            ))}
          </ul>
        )}

        <div className="grid grid-cols-2 gap-x-6 gap-y-3">
          {/* Valuation */}
          <Section title="Valuation">
            <MetricRow label="P/E" value={data.pe_ratio} formatter={ratio} />
            <MetricRow label="Fwd P/E" value={data.forward_pe} formatter={ratio} />
            <MetricRow label="PEG" value={data.peg_ratio} formatter={ratio} />
            <MetricRow label="P/B" value={data.price_to_book} formatter={ratio} />
          </Section>

          {/* Profitability */}
          <Section title="Profitability">
            <MetricRow label="Net Margin" value={data.profit_margin} formatter={pct} />
            <MetricRow label="Op. Margin" value={data.operating_margin} formatter={pct} />
            <MetricRow label="ROE" value={data.return_on_equity} formatter={pct} />
            <MetricRow label="ROA" value={data.return_on_assets} formatter={pct} />
          </Section>

          {/* Growth */}
          <Section title="Growth">
            <MetricRow label="Revenue" value={data.revenue_growth} formatter={pct} />
            <MetricRow label="Earnings" value={data.earnings_growth} formatter={pct} />
          </Section>

          {/* Health */}
          <Section title="Health">
            <MetricRow label="Current Ratio" value={data.current_ratio} formatter={ratio} />
            <MetricRow label="Debt/Equity" value={data.debt_to_equity} formatter={ratio} />
            <MetricRow label="Free Cash Flow" value={data.free_cash_flow} formatter={formatCash} />
          </Section>
        </div>
      </CardContent>
    </Card>
  );
}
