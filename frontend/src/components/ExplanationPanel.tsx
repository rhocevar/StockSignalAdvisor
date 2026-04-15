import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface ExplanationPanelProps {
  explanation: string;
}

/** Guard against raw JSON reaching the UI if backend parsing fails. */
function safeExplanation(text: string): string {
  if (!/"signal"\s*:/.test(text)) return text;
  try {
    const obj = JSON.parse(text.startsWith("{") ? text : "{" + text);
    if (typeof obj?.explanation === "string") return obj.explanation;
  } catch { /* fall through */ }
  return text;
}

export function ExplanationPanel({ explanation }: ExplanationPanelProps) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base font-semibold">AI Analysis</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground leading-relaxed whitespace-pre-wrap">
          {safeExplanation(explanation)}
        </p>
      </CardContent>
    </Card>
  );
}
