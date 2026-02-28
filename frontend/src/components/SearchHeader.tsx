"use client";

import { useState, useEffect, type KeyboardEvent } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export function SearchHeader() {
  const pathname = usePathname();
  const router = useRouter();

  const currentTicker =
    pathname.split("/analyze/")[1]?.toUpperCase() ?? "";

  const [ticker, setTicker] = useState(currentTicker);

  // Re-sync when the user navigates to a different ticker via this header
  useEffect(() => {
    setTicker(pathname.split("/analyze/")[1]?.toUpperCase() ?? "");
  }, [pathname]);

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const raw = e.target.value.toUpperCase().replace(/[^A-Z0-9.]/g, "");
    setTicker(raw);
  }

  function handleSubmit() {
    const trimmed = ticker.trim();
    if (!trimmed) return;
    router.push(`/analyze/${trimmed}`);
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
          <Input
            type="text"
            placeholder="Ticker..."
            value={ticker}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            maxLength={10}
            aria-label="Stock ticker symbol"
            className="w-28 sm:w-40 font-mono text-sm tracking-widest uppercase"
          />
          <Button
            onClick={handleSubmit}
            disabled={ticker.trim().length === 0}
            size="sm"
          >
            Analyze
          </Button>
        </div>
      </div>
    </header>
  );
}
