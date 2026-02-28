import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {
  RecentSearches,
  saveRecentTicker,
} from "../../components/RecentSearches";

const mockPush = jest.fn();

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

const STORAGE_KEY = "ssa_recent";

describe("saveRecentTicker", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("saves a ticker to localStorage", () => {
    saveRecentTicker("AAPL");
    const stored = JSON.parse(localStorage.getItem(STORAGE_KEY) ?? "[]");
    expect(stored).toEqual(["AAPL"]);
  });

  it("moves an existing ticker to the front (deduplicates)", () => {
    saveRecentTicker("AAPL");
    saveRecentTicker("NVDA");
    saveRecentTicker("AAPL");
    const stored = JSON.parse(localStorage.getItem(STORAGE_KEY) ?? "[]");
    expect(stored).toEqual(["AAPL", "NVDA"]);
  });

  it("limits the list to 5 entries, dropping the oldest", () => {
    ["A", "B", "C", "D", "E"].forEach(saveRecentTicker);
    saveRecentTicker("F");
    const stored = JSON.parse(localStorage.getItem(STORAGE_KEY) ?? "[]");
    expect(stored).toHaveLength(5);
    expect(stored[0]).toBe("F");
    expect(stored).not.toContain("A");
  });
});

describe("RecentSearches", () => {
  beforeEach(() => {
    localStorage.clear();
    mockPush.mockClear();
  });

  it("renders nothing when localStorage is empty", () => {
    const { container } = render(<RecentSearches />);
    expect(container.firstChild).toBeNull();
  });

  it("renders a chip for each stored ticker", () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(["AAPL", "NVDA", "TSLA"]));
    render(<RecentSearches />);
    expect(screen.getByText("AAPL")).toBeInTheDocument();
    expect(screen.getByText("NVDA")).toBeInTheDocument();
    expect(screen.getByText("TSLA")).toBeInTheDocument();
  });

  it("navigates to /analyze/[ticker] when a chip is clicked", async () => {
    const user = userEvent.setup();
    localStorage.setItem(STORAGE_KEY, JSON.stringify(["AAPL"]));
    render(<RecentSearches />);
    await user.click(screen.getByText("AAPL"));
    expect(mockPush).toHaveBeenCalledWith("/analyze/AAPL");
  });
});
