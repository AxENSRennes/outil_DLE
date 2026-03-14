import type { ReactNode } from "react";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, describe, expect, it, vi } from "vitest";

import { useBatchExecution, useStepDetail } from "../api/queries";

const batchExecutionPayload = {
  id: 1,
  batch_number: "LOT-2026-001",
  status: "in_progress",
  product_name: "Parfum 100mL",
  product_code: "CHR-PARF-100ML",
  site: { code: "CHR", name: "Chateau-Renard" },
  template_name: "Template pilot",
  template_code: "CHR-PILOT",
  steps: [],
  current_step_id: null,
  progress: { total: 0, completed: 0, applicable: 0 },
};

const stepDetailPayload = {
  id: 20,
  batch_id: 1,
  step_key: "weighing",
  sequence_order: 2,
  title: "Fichier de pesee",
  kind: "weighing",
  status: "in_progress",
  is_applicable: true,
  instructions: "Renseigner la pesee.",
  fields: [],
  signature_policy: { required: true, meaning: "performed_by" },
  blocking_policy: {
    blocks_execution_progress: false,
    blocks_step_completion: true,
    blocks_signature: true,
    blocks_pre_qa_handoff: true,
  },
  data: {},
  meta: {},
};

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

describe("execution queries", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("passes TanStack Query abort signal to batch execution fetch", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify(batchExecutionPayload), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      })
    );

    const { result } = renderHook(() => useBatchExecution(1), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    const [, requestInit] = fetchSpy.mock.calls[0] ?? [];
    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining("/batches/1/execution/"),
      expect.any(Object)
    );
    expect(requestInit).toMatchObject({ credentials: "include" });
    expect(requestInit?.signal).toBeInstanceOf(AbortSignal);
  });

  it("passes TanStack Query abort signal to step detail fetch", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify(stepDetailPayload), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      })
    );

    const { result } = renderHook(() => useStepDetail(20), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    const [, requestInit] = fetchSpy.mock.calls[0] ?? [];
    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining("/batches/steps/20/"),
      expect.any(Object)
    );
    expect(requestInit).toMatchObject({ credentials: "include" });
    expect(requestInit?.signal).toBeInstanceOf(AbortSignal);
  });
});
