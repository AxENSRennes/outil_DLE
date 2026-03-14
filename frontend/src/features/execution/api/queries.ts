import { useQuery } from "@tanstack/react-query";

import { appConfig } from "@/shared/config/app-config";
import { batchExecutionSchema, stepDetailSchema } from "../schemas/execution";
import type { BatchExecution, StepDetail } from "./types";

async function fetchBatchExecution(
  batchId: number,
  signal?: AbortSignal
): Promise<BatchExecution> {
  const response = await fetch(
    `${appConfig.apiBaseUrl}/batches/${batchId}/execution/`,
    { credentials: "include", signal }
  );
  if (!response.ok) {
    throw new Error(`Batch execution fetch failed: ${response.status}`);
  }
  const data: unknown = await response.json();
  return batchExecutionSchema.parse(data) as BatchExecution;
}

async function fetchStepDetail(
  stepId: number,
  signal?: AbortSignal
): Promise<StepDetail> {
  const response = await fetch(
    `${appConfig.apiBaseUrl}/batches/steps/${stepId}/`,
    { credentials: "include", signal }
  );
  if (!response.ok) {
    throw new Error(`Step detail fetch failed: ${response.status}`);
  }
  const data: unknown = await response.json();
  return stepDetailSchema.parse(data) as StepDetail;
}

export function useBatchExecution(batchId: number) {
  return useQuery({
    queryKey: ["batch-execution", batchId],
    queryFn: ({ signal }) => fetchBatchExecution(batchId, signal),
    enabled: batchId > 0,
  });
}

export function useStepDetail(stepId: number | null) {
  return useQuery({
    queryKey: ["step-detail", stepId],
    queryFn: ({ signal }) => {
      if (stepId == null) throw new Error("stepId is required");
      return fetchStepDetail(stepId, signal);
    },
    enabled: stepId != null && stepId > 0,
  });
}
