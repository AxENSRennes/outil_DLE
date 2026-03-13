import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi, beforeEach, type Mock } from "vitest";

import { PreQaReviewPage } from "@/features/pre-qa-review/routes/PreQaReviewPage";
import type { ReviewSummary } from "@/features/pre-qa-review/types";

// Mock the API hooks
vi.mock("@/features/pre-qa-review/api/use-review-summary", () => ({
  useReviewSummary: vi.fn(),
}));

vi.mock("@/features/pre-qa-review/api/use-confirm-pre-qa-review", () => ({
  useConfirmPreQaReview: vi.fn(),
}));

vi.mock("@/features/pre-qa-review/api/use-mark-step-reviewed", () => ({
  useMarkStepReviewed: vi.fn(),
}));

import { useReviewSummary } from "@/features/pre-qa-review/api/use-review-summary";
import { useConfirmPreQaReview } from "@/features/pre-qa-review/api/use-confirm-pre-qa-review";
import { useMarkStepReviewed } from "@/features/pre-qa-review/api/use-mark-step-reviewed";

const mockSummary: ReviewSummary = {
  batch_id: 42,
  batch_reference: "LOT-2026-0042",
  batch_status: "awaiting_pre_qa",
  severity: "amber",
  step_summary: { total: 3, not_started: 0, in_progress: 0, complete: 2, signed: 1 },
  flags: {
    missing_required_data: 0,
    missing_required_signatures: 0,
    changed_since_review: 1,
    changed_since_signature: 0,
    open_exceptions: 0,
    review_required: 0,
    blocking_open_exceptions: 0,
  },
  checklist: { expected_documents: 2, present_documents: 2, missing_documents: [] },
  flagged_steps: [
    {
      step_id: 5,
      step_reference: "Step 2 - Filling",
      step_status: "complete",
      flags: ["changed_since_review"],
      severity: "amber",
    },
  ],
};

function renderPage(batchId = "42") {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[`/review/${batchId}`]}>
        <Routes>
          <Route path="/review/:batchId" element={<PreQaReviewPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

const mockConfirmMutate = vi.fn();
const mockMarkReviewedMutate = vi.fn();

beforeEach(() => {
  vi.clearAllMocks();

  (useConfirmPreQaReview as Mock).mockReturnValue({
    mutate: mockConfirmMutate,
    isPending: false,
    isSuccess: false,
    error: null,
  });

  (useMarkStepReviewed as Mock).mockReturnValue({
    mutate: mockMarkReviewedMutate,
    isPending: false,
    isSuccess: false,
    error: null,
    variables: undefined,
  });
});

describe("PreQaReviewPage", () => {
  it("shows loading state", () => {
    (useReviewSummary as Mock).mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    });

    renderPage();
    expect(screen.getByText("Loading review summary...")).toBeInTheDocument();
  });

  it("shows error state", () => {
    (useReviewSummary as Mock).mockReturnValue({
      data: undefined,
      isLoading: false,
      error: { detail: "Batch not found." },
    });

    renderPage();
    expect(screen.getByText("Failed to load review summary")).toBeInTheDocument();
  });

  it("renders batch header with reference and severity", () => {
    (useReviewSummary as Mock).mockReturnValue({
      data: mockSummary,
      isLoading: false,
      error: null,
    });

    renderPage();
    expect(screen.getByText("LOT-2026-0042")).toBeInTheDocument();
    expect(screen.getByText("Warnings")).toBeInTheDocument();
  });

  it("renders flagged steps in exception list", () => {
    (useReviewSummary as Mock).mockReturnValue({
      data: mockSummary,
      isLoading: false,
      error: null,
    });

    renderPage();
    expect(screen.getByText("Step 2 - Filling")).toBeInTheDocument();
  });

  it("disables confirm button when severity is red", () => {
    const redSummary = {
      ...mockSummary,
      severity: "red" as const,
      flagged_steps: [
        {
          step_id: 1,
          step_reference: "Step 1",
          step_status: "in_progress",
          flags: ["missing_required_data"],
          severity: "red" as const,
        },
      ],
    };

    (useReviewSummary as Mock).mockReturnValue({
      data: redSummary,
      isLoading: false,
      error: null,
    });

    renderPage();
    const confirmButton = screen.getByText("Confirm Quality Handoff");
    expect(confirmButton.closest("button")).toBeDisabled();
  });

  it("enables confirm button when severity is amber or green", () => {
    (useReviewSummary as Mock).mockReturnValue({
      data: mockSummary,
      isLoading: false,
      error: null,
    });

    renderPage();
    const confirmButton = screen.getByText("Confirm Quality Handoff");
    expect(confirmButton.closest("button")).not.toBeDisabled();
  });

  it("shows confirm dialog when clicking confirm button", async () => {
    const user = userEvent.setup();
    (useReviewSummary as Mock).mockReturnValue({
      data: mockSummary,
      isLoading: false,
      error: null,
    });

    renderPage();
    await user.click(screen.getByText("Confirm Quality Handoff"));
    expect(screen.getByText(/This will confirm the batch/)).toBeInTheDocument();
    expect(screen.getByText("Confirm Handoff")).toBeInTheDocument();
  });

  it("calls confirmMutation when Confirm Handoff is clicked in dialog", async () => {
    const user = userEvent.setup();
    (useReviewSummary as Mock).mockReturnValue({
      data: mockSummary,
      isLoading: false,
      error: null,
    });

    renderPage();
    await user.click(screen.getByText("Confirm Quality Handoff"));
    await user.click(screen.getByText("Confirm Handoff"));
    expect(mockConfirmMutate).toHaveBeenCalledWith({ batchId: 42, note: "" });
  });

  it("calls confirmMutation with note when provided", async () => {
    const user = userEvent.setup();
    (useReviewSummary as Mock).mockReturnValue({
      data: mockSummary,
      isLoading: false,
      error: null,
    });

    renderPage();
    const noteInput = screen.getByPlaceholderText("Add a note about this review...");
    await user.type(noteInput, "Looks good");
    await user.click(screen.getByText("Confirm Quality Handoff"));
    await user.click(screen.getByText("Confirm Handoff"));
    expect(mockConfirmMutate).toHaveBeenCalledWith({ batchId: 42, note: "Looks good" });
  });

  it("shows invalid batch ID error for non-numeric batchId", () => {
    (useReviewSummary as Mock).mockReturnValue({
      data: undefined,
      isLoading: false,
      error: null,
    });

    renderPage("abc");
    expect(screen.getByText("Invalid batch ID")).toBeInTheDocument();
  });
});
