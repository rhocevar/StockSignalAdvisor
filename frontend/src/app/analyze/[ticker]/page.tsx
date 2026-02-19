interface AnalyzePageProps {
  params: { ticker: string };
}

export default function AnalyzePage({ params }: AnalyzePageProps) {
  const ticker = params.ticker.toUpperCase();

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8 font-[family-name:var(--font-geist-sans)]">
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold tracking-tight">{ticker}</h1>
        <p className="text-lg text-muted-foreground">
          Analysis results will appear here.
        </p>
      </div>
    </main>
  );
}
