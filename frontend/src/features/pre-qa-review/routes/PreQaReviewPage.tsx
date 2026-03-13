import { useState } from "react";
import { useParams } from "react-router-dom";
import { AlertTriangle, CheckCircle2, Loader2, XCircle } from "lucide-react";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/shared/ui/alert-dialog";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import { Separator } from "@/shared/ui/separator";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/shared/ui/tooltip";
import { useReviewSummary } from "@/features/pre-qa-review/api/use-review-summary";
import { useConfirmPreQaReview } from "@/features/pre-qa-review/api/use-confirm-pre-qa-review";
import { useMarkStepReviewed } from "@/features/pre-qa-review/api/use-mark-step-reviewed";
import { ReviewExceptionList } from "@/features/pre-qa-review/components/ReviewExceptionList";
import type { ApiError } from "@/shared/api/client";

const severityDisplay = {
  green: { icon: CheckCircle2, label: "Ready", className: "bg-green-600" },
  amber: { icon: AlertTriangle, label: "Warnings", className: "bg-amber-500 text-white" },
  red: { icon: XCircle, label: "Blocked", className: "" },
} as const;

export function PreQaReviewPage() {
  const { batchId } = useParams<{ batchId: string }>();
  const numericBatchId = Number(batchId);

  const [confirmNote, setConfirmNote] = useState("");

  const { data: summary, isLoading, error } = useReviewSummary(numericBatchId);
  const confirmMutation = useConfirmPreQaReview();
  const markReviewedMutation = useMarkStepReviewed();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        <span className="ml-2 text-muted-foreground">Loading review summary...</span>
      </div>
    );
  }

  if (error || !summary) {
    const apiError = error as unknown as ApiError | undefined;
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <XCircle className="h-8 w-8 text-destructive mx-auto mb-2" />
          <p className="text-destructive font-medium">Failed to load review summary</p>
          <p className="text-sm text-muted-foreground mt-1">
            {apiError?.detail ?? "An unexpected error occurred."}
          </p>
        </div>
      </div>
    );
  }

  const severityInfo = severityDisplay[summary.severity];
  const SeverityIcon = severityInfo.icon;
  const isConfirmDisabled = summary.severity === "red" || confirmMutation.isPending;

  function handleMarkReviewed(stepId: number) {
    markReviewedMutation.mutate({ batchId: numericBatchId, stepId });
  }

  function handleConfirm() {
    confirmMutation.mutate({
      batchId: numericBatchId,
      note: confirmNote,
    });
  }

  return (
    <div className="container mx-auto max-w-4xl py-6 space-y-6">
      {/* Batch Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-xl">Pre-QA Review</CardTitle>
              <p className="text-sm text-muted-foreground mt-1">
                {summary.batch_reference}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="outline">{summary.batch_status}</Badge>
              <Badge className={severityInfo.className} variant={summary.severity === "red" ? "destructive" : "default"}>
                <SeverityIcon className="h-3 w-3 mr-1" />
                {severityInfo.label}
              </Badge>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Exception List */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Review Items</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <ReviewExceptionList
            flaggedSteps={summary.flagged_steps}
            totalSteps={summary.step_summary.total}
            onMarkReviewed={handleMarkReviewed}
            isMarkingReviewed={markReviewedMutation.isPending}
          />
        </CardContent>
      </Card>

      {/* Mutation error display */}
      {(markReviewedMutation.error || confirmMutation.error) && (
        <div className="rounded-md border border-destructive bg-destructive/10 p-4">
          <p className="text-sm text-destructive font-medium">
            {(markReviewedMutation.error as unknown as ApiError)?.detail ??
              (confirmMutation.error as unknown as ApiError)?.detail ??
              "An error occurred."}
          </p>
        </div>
      )}

      {/* Confirm Handoff Section */}
      <Card>
        <CardContent className="pt-6">
          <div className="space-y-4">
            <div>
              <label htmlFor="confirm-note" className="text-sm font-medium">
                Reviewer Note (optional)
              </label>
              <textarea
                id="confirm-note"
                className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                rows={3}
                placeholder="Add a note about this review..."
                value={confirmNote}
                onChange={(e) => setConfirmNote(e.target.value)}
              />
            </div>

            <Separator />

            <div className="flex items-center justify-between">
              <div className="text-sm text-muted-foreground">
                {confirmMutation.isSuccess
                  ? "Handoff confirmed successfully."
                  : summary.severity === "red"
                    ? "Cannot confirm: blocking issues remain."
                    : "Ready to confirm quality handoff."}
              </div>

              {confirmMutation.isSuccess ? (
                <Badge className="bg-green-600">
                  <CheckCircle2 className="h-3 w-3 mr-1" />
                  Confirmed
                </Badge>
              ) : (
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <span tabIndex={isConfirmDisabled ? 0 : undefined}>
                        <AlertDialog>
                          <AlertDialogTrigger asChild>
                            <Button disabled={isConfirmDisabled}>
                              {confirmMutation.isPending ? (
                                <>
                                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                  Confirming...
                                </>
                              ) : (
                                "Confirm Quality Handoff"
                              )}
                            </Button>
                          </AlertDialogTrigger>
                          <AlertDialogContent>
                            <AlertDialogHeader>
                              <AlertDialogTitle>Confirm Quality Handoff</AlertDialogTitle>
                              <AlertDialogDescription>
                                This will confirm the batch "{summary.batch_reference}" as ready for quality review.
                                This action transitions the batch to "awaiting quality review" status.
                              </AlertDialogDescription>
                            </AlertDialogHeader>
                            <AlertDialogFooter>
                              <AlertDialogCancel>Cancel</AlertDialogCancel>
                              <AlertDialogAction onClick={handleConfirm}>
                                Confirm Handoff
                              </AlertDialogAction>
                            </AlertDialogFooter>
                          </AlertDialogContent>
                        </AlertDialog>
                      </span>
                    </TooltipTrigger>
                    {isConfirmDisabled && summary.severity === "red" && (
                      <TooltipContent>
                        Resolve blocking issues before confirming handoff
                      </TooltipContent>
                    )}
                  </Tooltip>
                </TooltipProvider>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
