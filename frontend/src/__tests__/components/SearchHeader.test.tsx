import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { SearchHeader } from "../../components/SearchHeader";

const mockPush = jest.fn();
let mockPathname = "/analyze/AAPL";

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
  usePathname: () => mockPathname,
}));

jest.mock("next/link", () => ({
  __esModule: true,
  default: ({ href, children }: { href: string; children: React.ReactNode }) => (
    <a href={href}>{children}</a>
  ),
}));

describe("SearchHeader", () => {
  beforeEach(() => {
    mockPush.mockClear();
    mockPathname = "/analyze/AAPL";
  });

  it("renders the app name as a link to home", () => {
    render(<SearchHeader />);
    const link = screen.getByRole("link", { name: /stock signal advisor/i });
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute("href", "/");
  });

  it("pre-fills the input with the ticker from the current pathname", () => {
    render(<SearchHeader />);
    expect(screen.getByRole("textbox")).toHaveValue("AAPL");
  });

  it("input is empty when pathname is not an analyze route", () => {
    mockPathname = "/";
    render(<SearchHeader />);
    expect(screen.getByRole("textbox")).toHaveValue("");
  });

  it("filters non-alphanumeric characters and uppercases input", async () => {
    const user = userEvent.setup();
    mockPathname = "/analyze/";
    render(<SearchHeader />);
    const input = screen.getByRole("textbox");
    await user.clear(input);
    await user.type(input, "msft!@#");
    expect(input).toHaveValue("MSFT");
  });

  it("disables the Analyze button when input is empty", () => {
    mockPathname = "/analyze/";
    render(<SearchHeader />);
    expect(screen.getByRole("button", { name: /analyze/i })).toBeDisabled();
  });

  it("navigates to /analyze/[ticker] on button click", async () => {
    const user = userEvent.setup();
    render(<SearchHeader />);
    await user.click(screen.getByRole("button", { name: /analyze/i }));
    expect(mockPush).toHaveBeenCalledWith("/analyze/AAPL");
  });

  it("navigates on Enter key press", async () => {
    const user = userEvent.setup();
    render(<SearchHeader />);
    await user.click(screen.getByRole("textbox"));
    await user.keyboard("{Enter}");
    expect(mockPush).toHaveBeenCalledWith("/analyze/AAPL");
  });

  it("does not navigate when input is empty", async () => {
    const user = userEvent.setup();
    mockPathname = "/analyze/";
    render(<SearchHeader />);
    await user.keyboard("{Enter}");
    expect(mockPush).not.toHaveBeenCalled();
  });
});
