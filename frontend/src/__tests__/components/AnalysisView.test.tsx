import { render, screen } from "../../test-utils";
import userEvent from "@testing-library/user-event";
import { AnalysisView } from "@/components/AnalysisView";
import { useStreamingAnalysis } from "@/hooks/useStreamingAnalysis";
import type { AnalyzeResponse } from "@/types";

jest.mock("../../hooks/useStreamingAnalysis");

const mockRestart = jest.fn();
const mockUseStreamingAnalysis = useStreamingAnalysis as jest.Mock;

const mockData: AnalyzeResponse = {
  ticker: "AAPL",
  company_name: "Apple Inc.",
  signal: "BUY",
  confidence: 0.85,
  explanation: "Strong technical signals across all indicators.",
  analysis: { technical: null, fundamentals: null, sentiment: null },
  price_data: {
    current: 150.0,
    currency: "USD",
    change_percent_1d: 1.2,
    change_percent_1w: null,
    change_percent_1m: null,
    high_52w: null,
    low_52w: null,
    price_history: [],
  },
  sources: [],
  metadata: {
    generated_at: "2025-01-01T00:00:00Z",
    llm_provider: "openai",
    model_used: "gpt-4o-mini",
    vectorstore_provider: "pinecone",
    cached: false,
  },
};

describe("AnalysisView", () => {
  beforeEach(() => {
    mockRestart.mockClear();
    mockUseStreamingAnalysis.mockReturnValue({
      technical: null,
      fundamental: null,
      sentimentData: null,
      result: null,
      isStreaming: false,
      error: null,
      restart: mockRestart,
    });
  });

  it("shows LoadingState when isStreaming is true and no data has arrived", () => {
    mockUseStreamingAnalysis.mockReturnValue({
      technical: null,
      fundamental: null,
      sentimentData: null,
      result: null,
      isStreaming: true,
      error: null,
      restart: mockRestart,
    });
    render(<AnalysisView ticker="AAPL" />);
    expect(screen.getByText(/AI analysis typically takes/i)).toBeInTheDocument();
  });

  it("shows error panel when error is set", () => {
    mockUseStreamingAnalysis.mockReturnValue({
      technical: null,
      fundamental: null,
      sentimentData: null,
      result: null,
      isStreaming: false,
      error: 'Ticker "XYZINVALID" not found.',
      restart: mockRestart,
    });
    render(<AnalysisView ticker="XYZINVALID" />);
    expect(screen.getByText(/Analysis failed/i)).toBeInTheDocument();
    expect(screen.getByText(/not found/i)).toBeInTheDocument();
  });

  it("shows Try Again button in error state that calls restart", async () => {
    const user = userEvent.setup();
    mockUseStreamingAnalysis.mockReturnValue({
      technical: null,
      fundamental: null,
      sentimentData: null,
      result: null,
      isStreaming: false,
      error: "Something went wrong",
      restart: mockRestart,
    });
    render(<AnalysisView ticker="AAPL" />);
    await user.click(screen.getByRole("button", { name: /try again/i }));
    expect(mockRestart).toHaveBeenCalled();
  });

  it("renders nothing when not streaming and no data or error", () => {
    render(<AnalysisView ticker="AAPL" />);
    expect(screen.queryByText(/AI analysis typically takes/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Analysis failed/i)).not.toBeInTheDocument();
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("renders signal card when result is present", () => {
    mockUseStreamingAnalysis.mockReturnValue({
      technical: null,
      fundamental: null,
      sentimentData: null,
      result: mockData,
      isStreaming: false,
      error: null,
      restart: mockRestart,
    });
    render(<AnalysisView ticker="AAPL" />);
    expect(screen.getByText("AAPL")).toBeInTheDocument();
    expect(screen.getByText("BUY")).toBeInTheDocument();
  });
});
