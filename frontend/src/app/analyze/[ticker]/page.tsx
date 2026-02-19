import { AnalysisView } from "@/components/AnalysisView";

interface AnalyzePageProps {
  params: { ticker: string };
}

export default function AnalyzePage({ params }: AnalyzePageProps) {
  return (
    <main className="flex min-h-screen flex-col items-center pt-16 pb-16 font-[family-name:var(--font-geist-sans)]">
      <AnalysisView ticker={params.ticker.toUpperCase()} />
    </main>
  );
}
