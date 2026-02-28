import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AnalysisView } from "@/components/AnalysisView";
import { useAnalysis } from "@/hooks/useAnalysis";
import type { AnalyzeResponse } from "@/types";

jest.mock("../../hooks/useAnalysis");

const mockRefetch = jest.fn();
const mockUseAnalysis = useAnalysis as jest.Mock;

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
    mockRefetch.mockClear();
    mockUseAnalysis.mockReturnValue({
      refetch: mockRefetch,
      isPending: false,
      data: undefined,
      error: null,
    });
  });

  it("shows LoadingState when isPending is true", () => {
    mockUseAnalysis.mockReturnValue({
      refetch: mockRefetch,
      isPending: true,
      data: undefined,
      error: null,
    });
    render(<AnalysisView ticker="AAPL" />);
    expect(screen.getByText(/AI analysis typically takes/i)).toBeInTheDocument();
  });

  it("shows error panel when error is set", () => {
    mockUseAnalysis.mockReturnValue({
      refetch: mockRefetch,
      isPending: false,
      data: undefined,
      error: new Error('Ticker "XYZINVALID" not found.'),
    });
    render(<AnalysisView ticker="XYZINVALID" />);
    expect(screen.getByText(/Analysis failed/i)).toBeInTheDocument();
    expect(screen.getByText(/not found/i)).toBeInTheDocument();
  });

  it("shows Try Again button in error state that calls refetch", async () => {
    const user = userEvent.setup();
    mockUseAnalysis.mockReturnValue({
      refetch: mockRefetch,
      isPending: false,
      data: undefined,
      error: new Error("Something went wrong"),
    });
    render(<AnalysisView ticker="AAPL" />);
    await user.click(screen.getByRole("button", { name: /try again/i }));
    expect(mockRefetch).toHaveBeenCalled();
  });

  it("renders nothing when not pending and no data or error", () => {
    render(<AnalysisView ticker="AAPL" />);
    expect(screen.queryByText(/AI analysis typically takes/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Analysis failed/i)).not.toBeInTheDocument();
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("renders signal card when analysis data is present", () => {
    mockUseAnalysis.mockReturnValue({
      refetch: mockRefetch,
      isPending: false,
      data: mockData,
      error: null,
    });
    render(<AnalysisView ticker="AAPL" />);
    expect(screen.getByText("AAPL")).toBeInTheDocument();
    expect(screen.getByText("BUY")).toBeInTheDocument();
  });
});
