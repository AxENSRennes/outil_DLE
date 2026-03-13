import { useState } from "react";
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
};

interface ReviewExceptionListProps {
  flaggedSteps: FlaggedStep[];
  totalSteps: number;
  onMarkReviewed: (stepId: number) => void;
  isMarkingReviewed: boolean;
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
        <Badge className="bg-amber-500 text-white">{amberCount} warnings</Badge>
        <Badge variant="destructive">{redCount} blocking</Badge>
      </div>
    </div>
  );
}

function FlaggedStepItem({
  step,
  onMarkReviewed,
  isMarkingReviewed,
}: {
  step: FlaggedStep;
  onMarkReviewed: (stepId: number) => void;
  isMarkingReviewed: boolean;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const config = severityConfig[step.severity];
  const SeverityIcon = config.icon;

  const hasReviewableFlags = step.flags.some(
    (f) => f === "changed_since_review" || f === "review_required",
  );

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <Card className="border-l-4" style={{ borderLeftColor: step.severity === "red" ? "var(--destructive)" : step.severity === "amber" ? "#f59e0b" : "#16a34a" }}>
        <CollapsibleTrigger asChild>
          <button
            className="flex w-full items-center gap-3 p-4 text-left hover:bg-muted/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            aria-expanded={isOpen}
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
                disabled={isMarkingReviewed}
              >
                {isMarkingReviewed ? "Marking..." : "Mark as Reviewed"}
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
  isMarkingReviewed,
}: ReviewExceptionListProps) {
  return (
    <div>
      <SummaryBar flaggedSteps={flaggedSteps} totalSteps={totalSteps} />
      <Separator />
      <ScrollArea className="h-[calc(100vh-320px)]">
        <div className="space-y-2 p-4">
          {flaggedSteps.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-8">
              No flagged steps. All steps are OK.
            </p>
          ) : (
            flaggedSteps.map((step) => (
              <FlaggedStepItem
                key={step.step_id}
                step={step}
                onMarkReviewed={onMarkReviewed}
                isMarkingReviewed={isMarkingReviewed}
              />
            ))
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
