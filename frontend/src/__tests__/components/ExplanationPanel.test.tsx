import { render, screen } from "@testing-library/react";
import { ExplanationPanel } from "../../components/ExplanationPanel";

describe("ExplanationPanel", () => {
  it("renders plain explanation text", () => {
    render(<ExplanationPanel explanation="Strong bullish signals across all pillars." />);
    expect(screen.getByText("Strong bullish signals across all pillars.")).toBeInTheDocument();
  });

  it("strips raw JSON and renders only the explanation field", () => {
    const rawJson =
      '"signal": "HOLD", "confidence": 0.56, "explanation": "Mixed outlook for BTC-USD."}';
    render(<ExplanationPanel explanation={rawJson} />);
    expect(screen.getByText("Mixed outlook for BTC-USD.")).toBeInTheDocument();
    expect(screen.queryByText(/"signal"/)).not.toBeInTheDocument();
  });

  it("strips well-formed JSON object and renders only the explanation field", () => {
    const rawJson = JSON.stringify({
      signal: "BUY",
      confidence: 0.75,
      explanation: "Bullish momentum confirmed.",
    });
    render(<ExplanationPanel explanation={rawJson} />);
    expect(screen.getByText("Bullish momentum confirmed.")).toBeInTheDocument();
    expect(screen.queryByText(/"signal"/)).not.toBeInTheDocument();
  });

  it("renders text unchanged when it contains no JSON signal key", () => {
    const explanation = "This stock shows strong momentum.";
    render(<ExplanationPanel explanation={explanation} />);
    expect(screen.getByText(explanation)).toBeInTheDocument();
  });
});
