import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { TickerInput } from "@/components/TickerInput";

const mockPush = jest.fn();

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

describe("TickerInput", () => {
  beforeEach(() => {
    mockPush.mockClear();
  });

  it("renders the input field and Analyze button", () => {
    render(<TickerInput />);
    expect(screen.getByRole("textbox")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /analyze/i })).toBeInTheDocument();
  });

  it("filters non-alphanumeric characters and uppercases input", async () => {
    const user = userEvent.setup();
    render(<TickerInput />);
    const input = screen.getByRole("textbox");
    await user.type(input, "aapl!@#");
    expect(input).toHaveValue("AAPL");
  });

  it("disables the Analyze button when input is empty", () => {
    render(<TickerInput />);
    expect(screen.getByRole("button", { name: /analyze/i })).toBeDisabled();
  });

  it("navigates to /analyze/AAPL on button click", async () => {
    const user = userEvent.setup();
    render(<TickerInput />);
    await user.type(screen.getByRole("textbox"), "AAPL");
    await user.click(screen.getByRole("button", { name: /analyze/i }));
    expect(mockPush).toHaveBeenCalledWith("/analyze/AAPL");
  });

  it("navigates on Enter key press", async () => {
    const user = userEvent.setup();
    render(<TickerInput />);
    await user.type(screen.getByRole("textbox"), "AAPL");
    await user.keyboard("{Enter}");
    expect(mockPush).toHaveBeenCalledWith("/analyze/AAPL");
  });
});
