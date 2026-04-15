import { render, screen } from "../../test-utils";
import { TechnicalIndicators } from "../../components/TechnicalIndicators";
import type { TechnicalAnalysis } from "../../types";

const fullData: TechnicalAnalysis = {
  rsi: 58.4,
  rsi_interpretation: "neutral",
  sma_50: 180.0,
  sma_200: 165.0,
  price_vs_sma50: "above",
  price_vs_sma200: "above",
  macd_signal: "bullish",
  volume_trend: "high",
  technical_score: 0.72,
};

const nullData: TechnicalAnalysis = {
  rsi: null,
  rsi_interpretation: null,
  sma_50: null,
  sma_200: null,
  price_vs_sma50: null,
  price_vs_sma200: null,
  macd_signal: null,
  volume_trend: null,
  technical_score: null,
};

describe("TechnicalIndicators", () => {
  it("renders the card title", () => {
    render(<TechnicalIndicators data={fullData} />);
    expect(screen.getByText("Technical Analysis")).toBeInTheDocument();
  });

  it("renders the bullishness score when provided", () => {
    render(<TechnicalIndicators data={fullData} />);
    expect(screen.getByText(/Bullishness Score \(72%\)/)).toBeInTheDocument();
  });

  it("does not render the score when technical_score is null", () => {
    render(<TechnicalIndicators data={nullData} />);
    expect(screen.queryByText(/Bullishness Score/)).not.toBeInTheDocument();
  });

  it("renders RSI value with interpretation", () => {
    render(<TechnicalIndicators data={fullData} />);
    expect(screen.getByText("58.4")).toBeInTheDocument();
    expect(screen.getByText("(neutral)")).toBeInTheDocument();
  });

  it("renders MACD badge", () => {
    render(<TechnicalIndicators data={fullData} />);
    expect(screen.getByText("bullish")).toBeInTheDocument();
  });

  it("renders SMA position badges", () => {
    render(<TechnicalIndicators data={fullData} />);
    const aboveBadges = screen.getAllByText("above");
    expect(aboveBadges).toHaveLength(2);
  });

  it("renders volume trend badge", () => {
    render(<TechnicalIndicators data={fullData} />);
    expect(screen.getByText("high")).toBeInTheDocument();
  });

  it("does not render RSI row when rsi is null", () => {
    render(<TechnicalIndicators data={nullData} />);
    expect(screen.queryByText("RSI")).not.toBeInTheDocument();
  });

  it("does not render MACD row when macd_signal is null", () => {
    render(<TechnicalIndicators data={nullData} />);
    expect(screen.queryByText("MACD")).not.toBeInTheDocument();
  });
});
