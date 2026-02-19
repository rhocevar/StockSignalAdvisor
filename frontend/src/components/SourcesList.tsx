import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { NewsSource, SentimentType } from "@/types";

interface SourcesListProps {
  sources: NewsSource[];
}

const sentimentStyles: Record<SentimentType, string> = {
  positive: "border-green-200 bg-green-50 text-green-700",
  negative: "border-red-200 bg-red-50 text-red-700",
  neutral: "border-gray-200 bg-gray-50 text-gray-600",
  mixed: "border-amber-200 bg-amber-50 text-amber-700",
};

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "";
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export function SourcesList({ sources }: SourcesListProps) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base font-semibold">
          News Sources ({sources.length})
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        {sources.length === 0 ? (
          <p className="text-sm text-muted-foreground px-6 pb-6">
            No news sources available.
          </p>
        ) : (
          <ul className="divide-y">
            {sources.map((source, index) => (
              <li
                key={index}
                className="px-6 py-3 flex items-start justify-between gap-4"
              >
                <div className="min-w-0 flex-1">
                  {source.url ? (
                    <a
                      href={source.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm font-medium hover:underline line-clamp-2"
                    >
                      {source.title}
                    </a>
                  ) : (
                    <p className="text-sm font-medium line-clamp-2">
                      {source.title}
                    </p>
                  )}
                  <p className="text-xs text-muted-foreground mt-0.5">
                    {[source.source, formatDate(source.published_at)]
                      .filter(Boolean)
                      .join(" · ")}
                  </p>
                </div>
                {source.sentiment && (
                  <Badge
                    variant="outline"
                    className={cn(
                      "shrink-0 text-xs capitalize",
                      sentimentStyles[source.sentiment]
                    )}
                  >
                    {source.sentiment}
                  </Badge>
                )}
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
