import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/shared/api/client";
import type { ReviewSummary } from "@/features/pre-qa-review/types";

export const reviewSummaryKeys = {
  detail: (batchId: number) => ["review-summary", batchId] as const,
};

export function useReviewSummary(batchId: number, options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: reviewSummaryKeys.detail(batchId),
    queryFn: () =>
      apiFetch<ReviewSummary>(`/batches/${batchId}/review-summary`),
    enabled: options?.enabled,
  });
}
