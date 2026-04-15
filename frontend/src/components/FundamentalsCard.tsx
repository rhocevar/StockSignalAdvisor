import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { InfoTooltip } from "@/components/InfoTooltip";
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
  tooltip?: string;
}

function MetricRow({ label, value, formatter, tooltip }: MetricRowProps) {
  if (value === null) return null;
  return (
    <div className="flex items-start justify-between py-0.5 gap-1">
      <span className="text-sm text-muted-foreground flex items-center min-w-0">
        {label}
        {tooltip && <InfoTooltip content={tooltip} />}
      </span>
      <span className="text-sm font-medium shrink-0">{formatter(value)}</span>
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
        <div className="flex items-center justify-between gap-2">
          <CardTitle className="text-base min-w-0 truncate">Fundamental Analysis</CardTitle>
          {scorePct !== null && (
            <span className="text-sm text-muted-foreground shrink-0 flex items-center">
              Bullishness Score ({scorePct}%)
              <InfoTooltip content="Composite 0–100% score across valuation, profitability, growth, and financial health. ≥60% is bullish, ≤40% is bearish." />
            </span>
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

        <div className="grid grid-cols-2 gap-x-4 sm:gap-x-6 gap-y-3">
          {/* Valuation */}
          <Section title="Valuation">
            <MetricRow label="P/E" value={data.pe_ratio} formatter={ratio}
              tooltip="Price-to-Earnings ratio. Compares stock price to annual earnings. Lower may indicate undervaluation, but varies by sector." />
            <MetricRow label="Fwd P/E" value={data.forward_pe} formatter={ratio}
              tooltip="Forward P/E uses projected earnings for the next 12 months. Lower than trailing P/E suggests expected earnings growth." />
            <MetricRow label="PEG" value={data.peg_ratio} formatter={ratio}
              tooltip="Price/Earnings-to-Growth ratio. Below 1.0 suggests the stock may be undervalued relative to its growth rate." />
            <MetricRow label="P/B" value={data.price_to_book} formatter={ratio}
              tooltip="Price-to-Book ratio. Compares stock price to net asset value. Below 1.0 means trading below book value." />
          </Section>

          {/* Profitability */}
          <Section title="Profitability">
            <MetricRow label="Net Margin" value={data.profit_margin} formatter={pct}
              tooltip="Net income as a percentage of revenue. Higher margins indicate a more profitable business." />
            <MetricRow label="Op. Margin" value={data.operating_margin} formatter={pct}
              tooltip="Operating income as a percentage of revenue. Measures core business profitability before interest and taxes." />
            <MetricRow label="ROE" value={data.return_on_equity} formatter={pct}
              tooltip="Return on Equity. Net income relative to shareholder equity. Higher values indicate efficient use of investor capital." />
            <MetricRow label="ROA" value={data.return_on_assets} formatter={pct}
              tooltip="Return on Assets. Net income relative to total assets. Measures how efficiently the company uses its assets to generate profit." />
          </Section>

          {/* Growth */}
          <Section title="Growth">
            <MetricRow label="Revenue" value={data.revenue_growth} formatter={pct}
              tooltip="Year-over-year revenue growth rate. Positive values indicate the business is expanding its top line." />
            <MetricRow label="Earnings" value={data.earnings_growth} formatter={pct}
              tooltip="Year-over-year earnings (EPS) growth rate. Strong earnings growth is a key driver of long-term stock appreciation." />
          </Section>

          {/* Health */}
          <Section title="Health">
            <MetricRow label="Current Ratio" value={data.current_ratio} formatter={ratio}
              tooltip="Current assets divided by current liabilities. Above 1.0 means the company can cover its short-term obligations." />
            <MetricRow label="Debt/Equity" value={data.debt_to_equity} formatter={ratio}
              tooltip="Total debt divided by shareholder equity. Lower values indicate less financial leverage and lower bankruptcy risk." />
            <MetricRow label="Free Cash Flow" value={data.free_cash_flow} formatter={formatCash}
              tooltip="Cash generated after capital expenditures. Positive FCF gives the company flexibility to invest, pay dividends, or reduce debt." />
          </Section>
        </div>
      </CardContent>
    </Card>
  );
}
