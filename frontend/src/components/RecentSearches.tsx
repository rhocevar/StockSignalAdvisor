"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Clock } from "lucide-react";
import { Badge } from "@/components/ui/badge";

const STORAGE_KEY = "ssa_recent";
const MAX_RECENT = 5;

export function saveRecentTicker(ticker: string): void {
  if (typeof window === "undefined") return;
  const prev: string[] = JSON.parse(
    localStorage.getItem(STORAGE_KEY) ?? "[]"
  );
  const updated = [ticker, ...prev.filter((t) => t !== ticker)].slice(
    0,
    MAX_RECENT
  );
  localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
}

export function RecentSearches() {
  const [mounted, setMounted] = useState(false);
  const [recents, setRecents] = useState<string[]>([]);
  const router = useRouter();

  useEffect(() => {
    setMounted(true);
    const stored: string[] = JSON.parse(
      localStorage.getItem(STORAGE_KEY) ?? "[]"
    );
    setRecents(stored);
  }, []);

  if (!mounted || recents.length === 0) return null;

  return (
    <div className="flex items-center gap-2 flex-wrap justify-center mt-3">
      <Clock className="h-3 w-3 text-muted-foreground shrink-0" />
      {recents.map((ticker) => (
        <Badge
          key={ticker}
          variant="outline"
          className="cursor-pointer font-mono hover:bg-accent transition-colors"
          onClick={() => router.push(`/analyze/${ticker}`)}
        >
          {ticker}
        </Badge>
      ))}
    </div>
  );
}
