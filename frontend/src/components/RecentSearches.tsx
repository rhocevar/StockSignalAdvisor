"use client";

import { useState, useEffect, useTransition } from "react";
import { useRouter } from "next/navigation";
import { Clock, LoaderCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

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
  const [loadingTicker, setLoadingTicker] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();
  const router = useRouter();

  useEffect(() => {
    setMounted(true);
    const stored: string[] = JSON.parse(
      localStorage.getItem(STORAGE_KEY) ?? "[]"
    );
    setRecents(stored);
  }, []);

  if (!mounted || recents.length === 0) return null;

  function handleClick(ticker: string) {
    if (isPending) return;
    setLoadingTicker(ticker);
    startTransition(() => {
      router.push(`/analyze/${ticker}`);
    });
  }

  return (
    <div className="flex items-center gap-2 flex-wrap justify-center mt-3">
      <Clock className="h-3 w-3 text-muted-foreground shrink-0" />
      {recents.map((ticker) => {
        const isLoading = isPending && loadingTicker === ticker;
        return (
          <Badge
            key={ticker}
            variant="outline"
            className={cn(
              "font-mono transition-colors min-w-[3rem] justify-center",
              isPending
                ? isLoading
                  ? "cursor-default"
                  : "opacity-40 cursor-default"
                : "cursor-pointer hover:bg-accent"
            )}
            onClick={() => handleClick(ticker)}
          >
            {isLoading ? (
              <LoaderCircle className="h-3 w-3 animate-spin" />
            ) : (
              ticker
            )}
          </Badge>
        );
      })}
    </div>
  );
}
