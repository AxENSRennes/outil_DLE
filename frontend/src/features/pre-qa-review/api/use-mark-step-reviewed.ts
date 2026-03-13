import { useMutation, useQueryClient } from "@tanstack/react-query";

import { apiFetch } from "@/shared/api/client";
import type { MarkStepReviewedResponse } from "@/features/pre-qa-review/types";
import { reviewSummaryKeys } from "@/features/pre-qa-review/api/use-review-summary";

interface MarkStepReviewedParams {
  batchId: number;
  stepId: number;
  note?: string;
}

export function useMarkStepReviewed() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ batchId, stepId, note = "" }: MarkStepReviewedParams) =>
      apiFetch<MarkStepReviewedResponse>(
        `/batches/${batchId}/review-items/${stepId}/mark-reviewed`,
        {
          method: "POST",
          body: JSON.stringify({ note }),
        },
      ),
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({
        queryKey: reviewSummaryKeys.detail(variables.batchId),
      });
    },
  });
}
