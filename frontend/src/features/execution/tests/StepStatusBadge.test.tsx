import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { StepStatusBadge } from "../components/StepStatusBadge";

describe("StepStatusBadge", () => {
  it("renders Not Started status with label", () => {
    render(<StepStatusBadge status="not_started" isApplicable={true} />);
    expect(screen.getByRole("status")).toHaveAttribute(
      "aria-label",
      "Not Started"
    );
    expect(screen.getByText("Not Started")).toBeInTheDocument();
  });

  it("renders In Progress status", () => {
    render(<StepStatusBadge status="in_progress" isApplicable={true} />);
    expect(screen.getByText("In Progress")).toBeInTheDocument();
  });

  it("renders Complete status", () => {
    render(<StepStatusBadge status="complete" isApplicable={true} />);
    expect(screen.getByText("Complete")).toBeInTheDocument();
  });

  it("renders Signed status", () => {
    render(<StepStatusBadge status="signed" isApplicable={true} />);
    expect(screen.getByText("Signed")).toBeInTheDocument();
  });

  it("renders N/A for non-applicable step", () => {
    render(<StepStatusBadge status="not_started" isApplicable={false} />);
    expect(screen.getByRole("status")).toHaveAttribute("aria-label", "N/A");
    expect(screen.getByText("N/A")).toBeInTheDocument();
  });

  it("renders compact mode without text label", () => {
    render(
      <StepStatusBadge status="complete" isApplicable={true} compact={true} />
    );
    expect(screen.getByRole("status")).toHaveAttribute(
      "aria-label",
      "Complete"
    );
    expect(screen.queryByText("Complete")).not.toBeInTheDocument();
  });
});
