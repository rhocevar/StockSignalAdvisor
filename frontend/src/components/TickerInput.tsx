"use client";

import { useState, type KeyboardEvent } from "react";
import { useRouter } from "next/navigation";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export function TickerInput() {
  const [ticker, setTicker] = useState<string>("");
  const router = useRouter();

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
    if (e.key === "Enter") {
      handleSubmit();
    }
  }

  return (
    <div className="flex w-full max-w-sm items-center gap-2">
      <Input
        type="text"
        placeholder="AAPL, NVDA, VOO..."
        value={ticker}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        maxLength={10}
        aria-label="Stock ticker symbol"
        className="font-mono text-base tracking-widest uppercase"
      />
      <Button onClick={handleSubmit} disabled={ticker.trim().length === 0}>
        Analyze
      </Button>
    </div>
  );
}
