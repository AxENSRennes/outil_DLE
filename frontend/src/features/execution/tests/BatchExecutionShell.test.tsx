import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, expect, it, vi, beforeEach } from "vitest";

import type { BatchExecution, StepDetail } from "../api/types";

const MOCK_BATCH: BatchExecution = {
  id: 1,
  batch_number: "LOT-2026-001",
  status: "in_progress",
  product_name: "Parfum 100mL",
  product_code: "CHR-PARF-100ML",
  site: { code: "CHR", name: "Chateau-Renard" },
  template_name: "Template pilot",
  template_code: "CHR-PILOT",
  steps: [
    {
      id: 10,
      step_key: "fabrication_bulk",
      sequence_order: 1,
      title: "Dossier de fabrication bulk",
      kind: "manufacturing",
      status: "complete",
      is_applicable: true,
      signature_state: "signed",
      requires_signature: true,
    },
    {
      id: 20,
      step_key: "weighing",
      sequence_order: 2,
      title: "Fichier de pesee",
      kind: "weighing",
      status: "in_progress",
      is_applicable: true,
      signature_state: "required",
      requires_signature: true,
    },
  ],
  current_step_id: 20,
  progress: { total: 2, completed: 1, applicable: 2 },
};

const MOCK_STEP_DETAIL: StepDetail = {
  id: 20,
  batch_id: 1,
  step_key: "weighing",
  sequence_order: 2,
  title: "Fichier de pesee",
  kind: "weighing",
  status: "in_progress",
  is_applicable: true,
  instructions: "Renseigner la pesee.",
  fields: [
    {
      key: "density",
      type: "decimal",
      label: "Densite",
      required: true,
    },
  ],
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

vi.mock("../api/queries", () => ({
  useBatchExecution: vi.fn(),
  useStepDetail: vi.fn(),
}));

import { useBatchExecution, useStepDetail } from "../api/queries";
import { BatchExecutionShell } from "../components/BatchExecutionShell";

const mockedUseBatchExecution = vi.mocked(useBatchExecution);
const mockedUseStepDetail = vi.mocked(useStepDetail);

function renderShell() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <BatchExecutionShell batchId={1} />
    </QueryClientProvider>
  );
}

describe("BatchExecutionShell", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders batch header and step content when loaded", () => {
    mockedUseBatchExecution.mockReturnValue({
      data: MOCK_BATCH,
      isLoading: false,
      error: null,
    } as ReturnType<typeof useBatchExecution>);
    mockedUseStepDetail.mockReturnValue({
      data: MOCK_STEP_DETAIL,
      isLoading: false,
      error: null,
    } as ReturnType<typeof useStepDetail>);

    renderShell();
    // LOT number appears in both sidebar header and batch header
    expect(screen.getAllByText("LOT-2026-001").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Parfum 100mL").length).toBeGreaterThanOrEqual(1);
    // Step title appears in sidebar and executor
    expect(screen.getAllByText("Fichier de pesee").length).toBeGreaterThanOrEqual(1);
  });

  it("shows loading state", () => {
    mockedUseBatchExecution.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    } as ReturnType<typeof useBatchExecution>);

    renderShell();
    // Skeleton elements should be present (no batch data yet)
    expect(screen.queryByText("LOT-2026-001")).not.toBeInTheDocument();
  });

  it("shows error state", () => {
    mockedUseBatchExecution.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error("Network error"),
    } as ReturnType<typeof useBatchExecution>);

    renderShell();
    expect(
      screen.getByText("Failed to load batch execution.")
    ).toBeInTheDocument();
  });

  it("auto-positions on current step", () => {
    mockedUseBatchExecution.mockReturnValue({
      data: MOCK_BATCH,
      isLoading: false,
      error: null,
    } as ReturnType<typeof useBatchExecution>);
    mockedUseStepDetail.mockReturnValue({
      data: MOCK_STEP_DETAIL,
      isLoading: false,
      error: null,
    } as ReturnType<typeof useStepDetail>);

    renderShell();
    // The current step (weighing, id=20) should have aria-current
    const activeButton = screen.getByRole("button", {
      name: /Fichier de pesee/,
    });
    expect(activeButton).toHaveAttribute("aria-current", "step");
  });
});
