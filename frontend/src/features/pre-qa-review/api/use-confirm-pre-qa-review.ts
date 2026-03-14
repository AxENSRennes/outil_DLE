import { useMutation, useQueryClient } from "@tanstack/react-query";

import { apiFetch } from "@/shared/api/client";
import type { PreQaReviewConfirmation } from "@/features/pre-qa-review/types";
import { reviewSummaryKeys } from "@/features/pre-qa-review/api/use-review-summary";

interface ConfirmPreQaReviewParams {
  batchId: number;
  note?: string;
}

export function useConfirmPreQaReview() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ batchId, note = "" }: ConfirmPreQaReviewParams) =>
      apiFetch<PreQaReviewConfirmation>(
        `/batches/${batchId}/pre-qa-review/confirm`,
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
