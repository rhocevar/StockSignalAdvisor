import { SearchHeader } from "@/components/SearchHeader";

export default function AnalyzeLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      <SearchHeader />
      {children}
    </>
  );
}
