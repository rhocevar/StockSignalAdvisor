import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { SignalType } from "@/types";

interface SignalBadgeProps {
  signal: SignalType;
  size?: "sm" | "default";
}

const signalStyles: Record<SignalType, string> = {
  STRONG_BUY: "border-green-500 bg-green-100 text-green-800 hover:bg-green-100 dark:bg-green-900/40 dark:text-green-300 dark:border-green-700 dark:hover:bg-green-900/40",
  BUY: "border-green-200 bg-green-50 text-green-700 hover:bg-green-50 dark:bg-green-950/40 dark:text-green-400 dark:border-green-800 dark:hover:bg-green-950/40",
  HOLD: "border-amber-200 bg-amber-50 text-amber-700 hover:bg-amber-50 dark:bg-amber-950/40 dark:text-amber-400 dark:border-amber-800 dark:hover:bg-amber-950/40",
  SELL: "border-red-200 bg-red-50 text-red-700 hover:bg-red-50 dark:bg-red-950/40 dark:text-red-400 dark:border-red-800 dark:hover:bg-red-950/40",
  STRONG_SELL: "border-red-500 bg-red-100 text-red-800 hover:bg-red-100 dark:bg-red-900/40 dark:text-red-300 dark:border-red-700 dark:hover:bg-red-900/40",
};

const signalLabel: Record<SignalType, string> = {
  STRONG_BUY: "STRONG BUY",
  BUY: "BUY",
  HOLD: "HOLD",
  SELL: "SELL",
  STRONG_SELL: "STRONG SELL",
};

export function SignalBadge({ signal, size = "default" }: SignalBadgeProps) {
  return (
    <Badge
      variant="outline"
      className={cn(
        signalStyles[signal],
        size === "sm" ? "text-xs px-2 py-0" : "text-sm px-3 py-1"
      )}
    >
      {signalLabel[signal]}
    </Badge>
  );
}
