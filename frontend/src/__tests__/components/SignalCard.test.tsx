import { render, screen, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { SignalCard } from "../../components/SignalCard";

const defaultProps = {
  ticker: "AAPL",
  companyName: "Apple Inc.",
  signal: "BUY" as const,
  confidence: 0.85,
  priceData: null,
};

describe("SignalCard", () => {
  it("renders the ticker and company name", () => {
    render(<SignalCard {...defaultProps} />);
    expect(screen.getByText("AAPL")).toBeInTheDocument();
    expect(screen.getByText("Apple Inc.")).toBeInTheDocument();
  });

  it("renders the signal badge", () => {
    render(<SignalCard {...defaultProps} />);
    expect(screen.getByText("BUY")).toBeInTheDocument();
  });

  it("renders the share button with 'Copy link' title", () => {
    render(<SignalCard {...defaultProps} />);
    expect(screen.getByTitle("Copy link")).toBeInTheDocument();
  });

  it("changes the button title to 'Copied!' immediately after click", async () => {
    const user = userEvent.setup();
    render(<SignalCard {...defaultProps} />);
    await user.click(screen.getByTitle("Copy link"));
    expect(screen.getByTitle("Copied!")).toBeInTheDocument();
  });

  it("reverts the button title back to 'Copy link' after 2 seconds", async () => {
    jest.useFakeTimers();
    const user = userEvent.setup({ delay: null });
    render(<SignalCard {...defaultProps} />);
    await user.click(screen.getByTitle("Copy link"));
    expect(screen.getByTitle("Copied!")).toBeInTheDocument();
    act(() => {
      jest.advanceTimersByTime(2000);
    });
    expect(screen.getByTitle("Copy link")).toBeInTheDocument();
    jest.useRealTimers();
  });
});
