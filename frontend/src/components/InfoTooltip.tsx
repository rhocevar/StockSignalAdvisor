import { Info } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface InfoTooltipProps {
  content: string;
}

export function InfoTooltip({ content }: InfoTooltipProps) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span className="inline-flex items-center cursor-help ml-1 text-muted-foreground/50 hover:text-muted-foreground transition-colors">
          <Info className="h-3 w-3" />
        </span>
      </TooltipTrigger>
      <TooltipContent className="max-w-56 text-center text-xs leading-snug">
        {content}
      </TooltipContent>
    </Tooltip>
  );
}
