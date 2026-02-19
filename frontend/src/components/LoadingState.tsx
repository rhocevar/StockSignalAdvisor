"use client";

import { useEffect, useState } from "react";
import { LoaderCircle } from "lucide-react";

const STATUS_STEPS = [
  "Fetching market data...",
  "Calculating technical indicators...",
  "Evaluating fundamentals...",
  "Analyzing news sentiment...",
  "Running AI analysis...",
  "Assembling recommendation...",
];

export function LoadingState() {
  const [stepIndex, setStepIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setStepIndex((prev) => (prev + 1) % STATUS_STEPS.length);
    }, 2500);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="w-full max-w-2xl mx-auto space-y-4 p-8">
      {/* Animated status indicator */}
      <div className="flex flex-col items-center gap-2 py-4">
        <LoaderCircle className="h-8 w-8 text-primary animate-spin" />
        <p className="text-sm font-medium text-foreground">
          {STATUS_STEPS[stepIndex]}
        </p>
        <p className="text-xs text-muted-foreground">
          AI analysis typically takes 10–20 seconds
        </p>
      </div>

      {/* Signal card skeleton */}
      <div className="rounded-xl border bg-card shadow p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <div className="h-5 w-32 bg-muted animate-pulse rounded" />
            <div className="h-4 w-20 bg-muted animate-pulse rounded" />
          </div>
          <div className="h-8 w-16 bg-muted animate-pulse rounded-md" />
        </div>
        <div className="flex items-center gap-4">
          <div className="h-8 w-24 bg-muted animate-pulse rounded" />
          <div className="h-6 w-16 bg-muted animate-pulse rounded" />
        </div>
        <div className="h-4 w-40 bg-muted animate-pulse rounded" />
      </div>

      {/* Price chart skeleton */}
      <div className="rounded-xl border bg-card shadow p-6 space-y-3">
        <div className="h-5 w-32 bg-muted animate-pulse rounded" />
        <div className="h-48 w-full bg-muted animate-pulse rounded-md" />
      </div>

      {/* Explanation skeleton */}
      <div className="rounded-xl border bg-card shadow p-6 space-y-3">
        <div className="h-5 w-28 bg-muted animate-pulse rounded" />
        <div className="space-y-2">
          <div className="h-4 w-full bg-muted animate-pulse rounded" />
          <div className="h-4 w-full bg-muted animate-pulse rounded" />
          <div className="h-4 w-3/4 bg-muted animate-pulse rounded" />
        </div>
      </div>

      {/* Technical indicators skeleton */}
      <div className="rounded-xl border bg-card shadow p-6 space-y-4">
        <div className="h-5 w-40 bg-muted animate-pulse rounded" />
        <div className="h-2 w-full bg-muted animate-pulse rounded-full" />
        <div className="grid grid-cols-2 gap-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="flex items-center justify-between">
              <div className="h-4 w-12 bg-muted animate-pulse rounded" />
              <div className="h-5 w-16 bg-muted animate-pulse rounded-md" />
            </div>
          ))}
        </div>
      </div>

      {/* Fundamentals skeleton */}
      <div className="rounded-xl border bg-card shadow p-6 space-y-4">
        <div className="h-5 w-44 bg-muted animate-pulse rounded" />
        <div className="h-2 w-full bg-muted animate-pulse rounded-full" />
        <div className="grid grid-cols-2 gap-3">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="flex items-center justify-between">
              <div className="h-4 w-20 bg-muted animate-pulse rounded" />
              <div className="h-4 w-14 bg-muted animate-pulse rounded" />
            </div>
          ))}
        </div>
      </div>

      {/* Sources skeleton */}
      <div className="rounded-xl border bg-card shadow p-6 space-y-3">
        <div className="h-5 w-24 bg-muted animate-pulse rounded" />
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="flex items-center justify-between py-2 border-b last:border-0"
          >
            <div className="space-y-1.5">
              <div className="h-4 w-48 bg-muted animate-pulse rounded" />
              <div className="h-3 w-24 bg-muted animate-pulse rounded" />
            </div>
            <div className="h-5 w-14 bg-muted animate-pulse rounded-md" />
          </div>
        ))}
      </div>
    </div>
  );
}
