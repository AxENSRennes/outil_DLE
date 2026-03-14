import { Badge } from "@/shared/ui/badge";
import type { BatchExecution } from "../api/types";

interface BatchHeaderProps {
  batch: BatchExecution;
}

export function BatchHeader({ batch }: BatchHeaderProps) {
  return (
    <header className="flex items-center justify-between border-b bg-background px-6 h-14 shrink-0">
      <div className="flex items-center gap-4">
        <h1 className="text-base font-semibold">{batch.batch_number}</h1>
        <span className="text-sm text-muted-foreground">
          {batch.product_name}
        </span>
        <Badge variant="secondary">{batch.status.replaceAll("_", " ")}</Badge>
      </div>
      <div className="text-sm text-muted-foreground">
        {batch.site.name} ({batch.site.code})
      </div>
    </header>
  );
}
