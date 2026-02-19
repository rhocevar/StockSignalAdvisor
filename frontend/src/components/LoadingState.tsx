export function LoadingState() {
  return (
    <div className="w-full max-w-2xl mx-auto space-y-4 p-8">
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
