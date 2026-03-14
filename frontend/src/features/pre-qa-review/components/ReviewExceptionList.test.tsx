import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ReviewExceptionList } from "@/features/pre-qa-review/components/ReviewExceptionList";
import type { FlaggedStep } from "@/features/pre-qa-review/types";

const flaggedSteps: FlaggedStep[] = [
  {
    step_id: 1,
    step_reference: "Step 1 - Mixing",
    step_status: "complete",
    flags: ["changed_since_review", "review_required"],
    severity: "amber",
  },
  {
    step_id: 2,
    step_reference: "Step 2 - Filling",
    step_status: "in_progress",
    flags: ["missing_required_data"],
    severity: "red",
  },
];

describe("ReviewExceptionList", () => {
  it("renders summary bar with correct counts", () => {
    render(
      <ReviewExceptionList
        flaggedSteps={flaggedSteps}
        totalSteps={5}
        onMarkReviewed={vi.fn()}
        markingStepId={null}
      />,
    );

    expect(screen.getByText("5 steps total")).toBeInTheDocument();
    expect(screen.getByText("3 OK")).toBeInTheDocument();
    expect(screen.getByText("1 warning")).toBeInTheDocument();
    expect(screen.getByText("1 blocking")).toBeInTheDocument();
  });

  it("renders plural warnings for multiple amber steps", () => {
    const multiAmber: FlaggedStep[] = [
      { step_id: 1, step_reference: "Step 1", step_status: "complete", flags: ["changed_since_review"], severity: "amber" },
      { step_id: 2, step_reference: "Step 2", step_status: "complete", flags: ["review_required"], severity: "amber" },
    ];
    render(
      <ReviewExceptionList
        flaggedSteps={multiAmber}
        totalSteps={5}
        onMarkReviewed={vi.fn()}
        markingStepId={null}
      />,
    );

    expect(screen.getByText("2 warnings")).toBeInTheDocument();
  });

  it("renders flagged step references", () => {
    render(
      <ReviewExceptionList
        flaggedSteps={flaggedSteps}
        totalSteps={5}
        onMarkReviewed={vi.fn()}
        markingStepId={null}
      />,
    );

    expect(screen.getByText("Step 1 - Mixing")).toBeInTheDocument();
    expect(screen.getByText("Step 2 - Filling")).toBeInTheDocument();
  });

  it("renders severity badges", () => {
    render(
      <ReviewExceptionList
        flaggedSteps={flaggedSteps}
        totalSteps={5}
        onMarkReviewed={vi.fn()}
        markingStepId={null}
      />,
    );

    expect(screen.getByText("Warning")).toBeInTheDocument();
    expect(screen.getByText("Blocking")).toBeInTheDocument();
  });

  it("shows mark-reviewed button on expand for reviewable step", async () => {
    const user = userEvent.setup();
    render(
      <ReviewExceptionList
        flaggedSteps={flaggedSteps}
        totalSteps={5}
        onMarkReviewed={vi.fn()}
        markingStepId={null}
      />,
    );

    // Expand the amber step (has reviewable flags)
    await user.click(screen.getByText("Step 1 - Mixing"));
    expect(screen.getByText("Mark as Reviewed")).toBeInTheDocument();
  });

  it("calls onMarkReviewed when mark-reviewed button is clicked", async () => {
    const user = userEvent.setup();
    const onMarkReviewed = vi.fn();

    render(
      <ReviewExceptionList
        flaggedSteps={flaggedSteps}
        totalSteps={5}
        onMarkReviewed={onMarkReviewed}
        markingStepId={null}
      />,
    );

    await user.click(screen.getByText("Step 1 - Mixing"));
    await user.click(screen.getByText("Mark as Reviewed"));
    expect(onMarkReviewed).toHaveBeenCalledWith(1);
  });

  it("shows empty message when no flagged steps", () => {
    render(
      <ReviewExceptionList
        flaggedSteps={[]}
        totalSteps={3}
        onMarkReviewed={vi.fn()}
        markingStepId={null}
      />,
    );

    expect(screen.getByText("No flagged review items.")).toBeInTheDocument();
  });

  it("disables only the step being marked as reviewed", async () => {
    const user = userEvent.setup();
    render(
      <ReviewExceptionList
        flaggedSteps={flaggedSteps}
        totalSteps={5}
        onMarkReviewed={vi.fn()}
        markingStepId={1}
      />,
    );

    await user.click(screen.getByText("Step 1 - Mixing"));
    const button = screen.getByText("Marking...");
    expect(button.closest("button")).toBeDisabled();
  });

  it("navigates between items with arrow keys", async () => {
    const user = userEvent.setup();
    render(
      <ReviewExceptionList
        flaggedSteps={flaggedSteps}
        totalSteps={5}
        onMarkReviewed={vi.fn()}
        markingStepId={null}
      />,
    );

    // Focus first item
    const firstButton = screen.getByText("Step 1 - Mixing").closest("button")!;
    firstButton.focus();
    expect(firstButton).toHaveFocus();

    // Arrow down → second item
    await user.keyboard("{ArrowDown}");
    const secondButton = screen.getByText("Step 2 - Filling").closest("button")!;
    expect(secondButton).toHaveFocus();

    // Arrow up → back to first
    await user.keyboard("{ArrowUp}");
    expect(firstButton).toHaveFocus();
  });

  it("renders an incomplete badge for incomplete steps", async () => {
    const user = userEvent.setup();
    const incompleteSteps: FlaggedStep[] = [
      {
        step_id: 3,
        step_reference: "Step 3 - Preparation",
        step_status: "not_started",
        flags: ["step_incomplete"],
        severity: "amber",
      },
    ];

    render(
      <ReviewExceptionList
        flaggedSteps={incompleteSteps}
        totalSteps={3}
        onMarkReviewed={vi.fn()}
        markingStepId={null}
      />,
    );

    await user.click(screen.getByText("Step 3 - Preparation"));
    expect(screen.getByText("Incomplete")).toBeInTheDocument();
  });
});
