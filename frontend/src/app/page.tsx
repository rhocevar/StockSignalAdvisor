export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8 font-[family-name:var(--font-geist-sans)]">
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold tracking-tight">
          Stock Signal Advisor
        </h1>
        <p className="text-lg text-muted-foreground max-w-md">
          AI-powered stock analysis with technical, fundamental, and sentiment
          insights.
        </p>
      </div>
    </main>
  );
}
