import { useRef, useState } from "react";
import { ChevronDown, ChevronRight, CheckCircle2, AlertTriangle, XCircle } from "lucide-react";

import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card, CardContent } from "@/shared/ui/card";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/shared/ui/collapsible";
import { ScrollArea } from "@/shared/ui/scroll-area";
import { Separator } from "@/shared/ui/separator";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/shared/ui/tooltip";
import type { FlaggedStep } from "@/features/pre-qa-review/types";

const severityConfig = {
  green: { icon: CheckCircle2, label: "OK", variant: "default" as const, className: "bg-green-600" },
  amber: { icon: AlertTriangle, label: "Warning", variant: "secondary" as const, className: "bg-amber-500 text-white" },
  red: { icon: XCircle, label: "Blocking", variant: "destructive" as const, className: "" },
} as const;

const flagLabels: Record<string, string> = {
  missing_required_data: "Missing Data",
  missing_required_signature: "Unsigned",
  changed_since_review: "Changed Since Review",
  changed_since_signature: "Changed Since Signature",
  review_required: "Review Required",
  open_exception: "Open Exception",
  step_incomplete: "Incomplete",
};

interface ReviewExceptionListProps {
  flaggedSteps: FlaggedStep[];
  totalSteps: number;
  onMarkReviewed: (stepId: number) => void;
  markingStepId: number | null;
}

function SummaryBar({ flaggedSteps, totalSteps }: { flaggedSteps: FlaggedStep[]; totalSteps: number }) {
  const greenCount = totalSteps - flaggedSteps.length;
  const amberCount = flaggedSteps.filter((s) => s.severity === "amber").length;
  const redCount = flaggedSteps.filter((s) => s.severity === "red").length;

  return (
    <div className="flex items-center gap-4 p-4" role="status" aria-label="Step summary">
      <span className="text-sm font-medium">{totalSteps} steps total</span>
      <Separator orientation="vertical" className="h-5" />
      <div className="flex gap-3">
        <Badge className="bg-green-600">{greenCount} OK</Badge>
        <Badge className="bg-amber-500 text-white">{amberCount} {amberCount === 1 ? "warning" : "warnings"}</Badge>
        <Badge variant="destructive">{redCount} blocking</Badge>
      </div>
    </div>
  );
}

function FlaggedStepItem({
  step,
  onMarkReviewed,
  markingStepId,
  index,
  itemRefs,
}: {
  step: FlaggedStep;
  onMarkReviewed: (stepId: number) => void;
  markingStepId: number | null;
  index: number;
  itemRefs: React.MutableRefObject<(HTMLButtonElement | null)[]>;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const config = severityConfig[step.severity];
  const SeverityIcon = config.icon;
  const isThisStepMarking = markingStepId === step.step_id;

  const hasReviewableFlags = step.flags.some(
    (f) => f === "changed_since_review" || f === "review_required",
  );

  function handleKeyDown(e: React.KeyboardEvent<HTMLButtonElement>) {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      const next = itemRefs.current[index + 1];
      next?.focus();
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      const prev = itemRefs.current[index - 1];
      prev?.focus();
    }
  }

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <Card className="border-l-4" style={{ borderLeftColor: step.severity === "red" ? "var(--destructive)" : step.severity === "amber" ? "#f59e0b" : "#16a34a" }}>
        <CollapsibleTrigger asChild>
          <button
            ref={(el) => { itemRefs.current[index] = el; }}
            className="flex w-full items-center gap-3 p-4 text-left hover:bg-muted/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            aria-expanded={isOpen}
            onKeyDown={handleKeyDown}
          >
            {isOpen ? <ChevronDown className="h-4 w-4 shrink-0" /> : <ChevronRight className="h-4 w-4 shrink-0" />}
            <SeverityIcon className="h-4 w-4 shrink-0" />
            <span className="flex-1 font-medium">{step.step_reference}</span>
            <Badge className={config.className} variant={config.variant}>
              {config.label}
            </Badge>
          </button>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <CardContent className="pt-0 pb-4">
            <div className="flex flex-wrap gap-2 mb-3">
              {step.flags.map((flag) => (
                <TooltipProvider key={flag}>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Badge variant="outline">{flagLabels[flag] ?? flag}</Badge>
                    </TooltipTrigger>
                    <TooltipContent>{flag}</TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              ))}
            </div>
            <div className="text-sm text-muted-foreground mb-3">
              Status: {step.step_status}
            </div>
            {hasReviewableFlags && (
              <Button
                size="sm"
                variant="outline"
                onClick={(e) => {
                  e.stopPropagation();
                  onMarkReviewed(step.step_id);
                }}
                disabled={isThisStepMarking}
              >
                {isThisStepMarking ? "Marking..." : "Mark as Reviewed"}
              </Button>
            )}
          </CardContent>
        </CollapsibleContent>
      </Card>
    </Collapsible>
  );
}

export function ReviewExceptionList({
  flaggedSteps,
  totalSteps,
  onMarkReviewed,
  markingStepId,
}: ReviewExceptionListProps) {
  const itemRefs = useRef<(HTMLButtonElement | null)[]>([]);

  return (
    <div>
      <SummaryBar flaggedSteps={flaggedSteps} totalSteps={totalSteps} />
      <Separator />
      <ScrollArea className="h-[calc(100vh-320px)]">
        <div className="space-y-2 p-4">
          {flaggedSteps.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-8">
              No flagged review items.
            </p>
          ) : (
            flaggedSteps.map((step, index) => (
              <FlaggedStepItem
                key={step.step_id}
                step={step}
                onMarkReviewed={onMarkReviewed}
                markingStepId={markingStepId}
                index={index}
                itemRefs={itemRefs}
              />
            ))
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
