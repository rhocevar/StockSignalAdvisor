"use client";

import { useState, useEffect, useTransition, type KeyboardEvent } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { LoaderCircle, Sun, Moon } from "lucide-react";
import { useTheme } from "next-themes";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export function SearchHeader() {
  const pathname = usePathname();
  const router = useRouter();
  const [isPending, startTransition] = useTransition();

  const currentTicker =
    decodeURIComponent(pathname.split("/analyze/")[1] ?? "").toUpperCase();

  const [ticker, setTicker] = useState(currentTicker);
  const { resolvedTheme, setTheme } = useTheme();

  // Re-sync when the user navigates to a different ticker via this header
  useEffect(() => {
    setTicker(decodeURIComponent(pathname.split("/analyze/")[1] ?? "").toUpperCase());
  }, [pathname]);

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const raw = e.target.value.toUpperCase().replace(/[^A-Z0-9.^=-]/g, "");
    setTicker(raw);
  }

  function handleSubmit() {
    const trimmed = ticker.trim();
    if (!trimmed) return;
    startTransition(() => {
      router.push(`/analyze/${trimmed}`);
    });
  }

  function handleKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") handleSubmit();
  }

  return (
    <header className="sticky top-0 z-10 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex items-center justify-between h-14 px-4 sm:px-6 max-w-5xl mx-auto">
        <Link
          href="/"
          className="text-sm font-semibold tracking-tight hover:text-primary transition-colors"
        >
          Stock Signal Advisor
        </Link>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setTheme(resolvedTheme === "dark" ? "light" : "dark")}
            aria-label="Toggle theme"
            className="h-8 w-8 shrink-0"
          >
            <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
            <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
          </Button>
          <Input
            type="text"
            placeholder="Ticker..."
            value={ticker}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            maxLength={12}
            aria-label="Stock ticker symbol"
            className="w-28 sm:w-40 font-mono text-sm tracking-widest uppercase"
          />
          <Button
            onClick={handleSubmit}
            disabled={ticker.trim().length === 0 || isPending}
            size="sm"
            className="min-w-20"
          >
            {isPending ? (
              <LoaderCircle className="h-4 w-4 animate-spin" />
            ) : (
              "Analyze"
            )}
          </Button>
        </div>
      </div>
    </header>
  );
}
