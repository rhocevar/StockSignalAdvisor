import { render, screen } from "@testing-library/react";
import { SignalBadge } from "@/components/SignalBadge";

describe("SignalBadge", () => {
  it("renders BUY with green styling", () => {
    render(<SignalBadge signal="BUY" />);
    const badge = screen.getByText("BUY");
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass("text-green-700");
  });

  it("renders SELL with red styling", () => {
    render(<SignalBadge signal="SELL" />);
    const badge = screen.getByText("SELL");
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass("text-red-700");
  });

  it("renders HOLD with amber styling", () => {
    render(<SignalBadge signal="HOLD" />);
    const badge = screen.getByText("HOLD");
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass("text-amber-700");
  });
});
