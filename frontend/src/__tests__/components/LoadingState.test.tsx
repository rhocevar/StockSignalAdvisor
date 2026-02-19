import { render, screen } from "@testing-library/react";
import { LoadingState } from "@/components/LoadingState";

describe("LoadingState", () => {
  it("renders without crashing", () => {
    const { container } = render(<LoadingState />);
    expect(container.firstChild).toBeInTheDocument();
  });

  it("shows an analysis in-progress message", () => {
    render(<LoadingState />);
    expect(
      screen.getByText(/AI analysis typically takes/i)
    ).toBeInTheDocument();
  });
});
