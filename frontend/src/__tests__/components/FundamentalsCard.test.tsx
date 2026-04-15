import { render, screen } from "../../test-utils";
import { FundamentalsCard } from "../../components/FundamentalsCard";
import type { FundamentalAnalysis } from "../../types";

const fullData: FundamentalAnalysis = {
  pe_ratio: 28.5,
  forward_pe: 24.1,
  peg_ratio: 1.8,
  price_to_book: 3.2,
  price_to_sales: null,
  enterprise_to_ebitda: null,
  profit_margin: 0.243,
  operating_margin: 0.301,
  gross_margin: null,
  return_on_equity: 0.147,
  return_on_assets: 0.082,
  revenue_growth: 0.08,
  earnings_growth: 0.12,
  earnings_quarterly_growth: null,
  current_ratio: 1.5,
  debt_to_equity: 0.45,
  free_cash_flow: 5_200_000_000,
  operating_cash_flow: null,
  dividend_yield: null,
  dividend_payout_ratio: null,
  market_cap: null,
  enterprise_value: null,
  shares_outstanding: null,
  float_shares: null,
  analyst_target: null,
  analyst_rating: null,
  number_of_analysts: null,
  fundamental_score: 0.68,
  insights: ["Strong profit margins", "Low leverage"],
};

const nullData: FundamentalAnalysis = {
  pe_ratio: null,
  forward_pe: null,
  peg_ratio: null,
  price_to_book: null,
  price_to_sales: null,
  enterprise_to_ebitda: null,
  profit_margin: null,
  operating_margin: null,
  gross_margin: null,
  return_on_equity: null,
  return_on_assets: null,
  revenue_growth: null,
  earnings_growth: null,
  earnings_quarterly_growth: null,
  current_ratio: null,
  debt_to_equity: null,
  free_cash_flow: null,
  operating_cash_flow: null,
  dividend_yield: null,
  dividend_payout_ratio: null,
  market_cap: null,
  enterprise_value: null,
  shares_outstanding: null,
  float_shares: null,
  analyst_target: null,
  analyst_rating: null,
  number_of_analysts: null,
  fundamental_score: null,
  insights: [],
};

describe("FundamentalsCard", () => {
  it("renders the card title", () => {
    render(<FundamentalsCard data={fullData} />);
    expect(screen.getByText("Fundamental Analysis")).toBeInTheDocument();
  });

  it("renders the bullishness score when provided", () => {
    render(<FundamentalsCard data={fullData} />);
    expect(screen.getByText(/Bullishness Score \(68%\)/)).toBeInTheDocument();
  });

  it("does not render the score when fundamental_score is null", () => {
    render(<FundamentalsCard data={nullData} />);
    expect(screen.queryByText(/Bullishness Score/)).not.toBeInTheDocument();
  });

  it("renders insights", () => {
    render(<FundamentalsCard data={fullData} />);
    expect(screen.getByText("Strong profit margins")).toBeInTheDocument();
    expect(screen.getByText("Low leverage")).toBeInTheDocument();
  });

  it("renders valuation metrics", () => {
    render(<FundamentalsCard data={fullData} />);
    expect(screen.getByText("28.50")).toBeInTheDocument(); // P/E
    expect(screen.getByText("24.10")).toBeInTheDocument(); // Fwd P/E
  });

  it("renders profitability metrics as percentages", () => {
    render(<FundamentalsCard data={fullData} />);
    expect(screen.getByText("24.3%")).toBeInTheDocument(); // Net Margin
    expect(screen.getByText("30.1%")).toBeInTheDocument(); // Op. Margin
  });

  it("renders free cash flow in human-readable format", () => {
    render(<FundamentalsCard data={fullData} />);
    expect(screen.getByText("$5.2B")).toBeInTheDocument();
  });

  it("suppresses metric rows when their value is null", () => {
    render(<FundamentalsCard data={nullData} />);
    expect(screen.queryByText("P/E")).not.toBeInTheDocument();
    expect(screen.queryByText("Net Margin")).not.toBeInTheDocument();
    expect(screen.queryByText("Free Cash Flow")).not.toBeInTheDocument();
  });
});
