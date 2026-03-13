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
        isMarkingReviewed={false}
      />,
    );

    expect(screen.getByText("5 steps total")).toBeInTheDocument();
    expect(screen.getByText("3 OK")).toBeInTheDocument();
    expect(screen.getByText("1 warnings")).toBeInTheDocument();
    expect(screen.getByText("1 blocking")).toBeInTheDocument();
  });

  it("renders flagged step references", () => {
    render(
      <ReviewExceptionList
        flaggedSteps={flaggedSteps}
        totalSteps={5}
        onMarkReviewed={vi.fn()}
        isMarkingReviewed={false}
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
        isMarkingReviewed={false}
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
        isMarkingReviewed={false}
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
        isMarkingReviewed={false}
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
        isMarkingReviewed={false}
      />,
    );

    expect(screen.getByText(/No flagged steps/)).toBeInTheDocument();
  });

  it("disables mark-reviewed button when isMarkingReviewed is true", async () => {
    const user = userEvent.setup();
    render(
      <ReviewExceptionList
        flaggedSteps={flaggedSteps}
        totalSteps={5}
        onMarkReviewed={vi.fn()}
        isMarkingReviewed={true}
      />,
    );

    await user.click(screen.getByText("Step 1 - Mixing"));
    const button = screen.getByText("Marking...");
    expect(button.closest("button")).toBeDisabled();
  });
});
