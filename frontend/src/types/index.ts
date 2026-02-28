// Enums (matching backend app/enums.py)
export type SignalType = "STRONG_BUY" | "BUY" | "HOLD" | "SELL" | "STRONG_SELL";
export type SentimentType = "positive" | "negative" | "neutral" | "mixed";
export type TrendDirection = "above" | "below";
export type MacdSignal = "bullish" | "bearish" | "neutral";
export type VolumeTrend = "high" | "low" | "neutral";

// Domain models (matching backend app/models/domain.py)

export interface TechnicalAnalysis {
  rsi: number | null;
  rsi_interpretation: string | null;
  sma_50: number | null;
  sma_200: number | null;
  price_vs_sma50: TrendDirection | null;
  price_vs_sma200: TrendDirection | null;
  macd_signal: MacdSignal | null;
  volume_trend: VolumeTrend | null;
  technical_score: number | null;
}

export interface FundamentalAnalysis {
  // Valuation
  pe_ratio: number | null;
  forward_pe: number | null;
  peg_ratio: number | null;
  price_to_book: number | null;
  price_to_sales: number | null;
  enterprise_to_ebitda: number | null;
  // Profitability
  profit_margin: number | null;
  operating_margin: number | null;
  gross_margin: number | null;
  return_on_equity: number | null;
  return_on_assets: number | null;
  // Growth
  revenue_growth: number | null;
  earnings_growth: number | null;
  earnings_quarterly_growth: number | null;
  // Financial Health
  current_ratio: number | null;
  debt_to_equity: number | null;
  free_cash_flow: number | null;
  operating_cash_flow: number | null;
  // Dividends
  dividend_yield: number | null;
  dividend_payout_ratio: number | null;
  // Size & Market
  market_cap: number | null;
  enterprise_value: number | null;
  shares_outstanding: number | null;
  float_shares: number | null;
  // Analyst
  analyst_target: number | null;
  analyst_rating: number | null;
  number_of_analysts: number | null;
  // Derived
  fundamental_score: number | null;
  insights: string[];
}

export interface SentimentAnalysis {
  overall: SentimentType | null;
  score: number | null;
  positive_count: number;
  negative_count: number;
  neutral_count: number;
}

export interface AnalysisResult {
  technical: TechnicalAnalysis | null;
  fundamentals: FundamentalAnalysis | null;
  sentiment: SentimentAnalysis | null;
}

export interface PricePoint {
  date: string;
  close: number;
}

export interface PriceData {
  current: number | null;
  currency: string;
  change_percent_1d: number | null;
  change_percent_1w: number | null;
  change_percent_1m: number | null;
  high_52w: number | null;
  low_52w: number | null;
  price_history: PricePoint[] | null;
}

export interface NewsSource {
  type: string;
  title: string;
  source: string | null;
  url: string | null;
  sentiment: SentimentType | null;
  published_at: string | null;
}

export interface AnalysisMetadata {
  generated_at: string;
  llm_provider: string;
  model_used: string;
  vectorstore_provider: string;
  cached: boolean;
}

// Request / Response (matching backend app/models/request.py & response.py)

export interface AnalyzeRequest {
  ticker: string;
  include_news?: boolean;
  include_technicals?: boolean;
  include_fundamentals?: boolean;
}

export interface AnalyzeResponse {
  ticker: string;
  company_name: string | null;
  signal: SignalType;
  confidence: number;
  explanation: string;
  analysis: AnalysisResult;
  price_data: PriceData | null;
  sources: NewsSource[];
  metadata: AnalysisMetadata;
}
