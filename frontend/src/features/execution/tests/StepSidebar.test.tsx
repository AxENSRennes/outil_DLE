import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { SidebarProvider } from "@/shared/ui/sidebar";
import { StepSidebar } from "../components/StepSidebar";
import type { BatchExecution } from "../api/types";

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
    {
      id: 30,
      step_key: "packaging",
      sequence_order: 3,
      title: "Execution conditionnement",
      kind: "packaging",
      status: "not_started",
      is_applicable: true,
      signature_state: "required",
      requires_signature: true,
    },
  ],
  current_step_id: 20,
  progress: { total: 3, completed: 1, applicable: 3 },
};

function renderSidebar(
  props: Partial<{
    activeStepId: number | null;
    onStepSelect: (id: number) => void;
  }> = {}
) {
  const onStepSelect = props.onStepSelect ?? vi.fn();
  return render(
    <SidebarProvider>
      <StepSidebar
        batch={MOCK_BATCH}
        activeStepId={props.activeStepId ?? 20}
        onStepSelect={onStepSelect}
      />
    </SidebarProvider>
  );
}

describe("StepSidebar", () => {
  it("renders all steps with correct titles", () => {
    renderSidebar();
    expect(
      screen.getByText("Dossier de fabrication bulk")
    ).toBeInTheDocument();
    expect(screen.getByText("Fichier de pesee")).toBeInTheDocument();
    expect(
      screen.getByText("Execution conditionnement")
    ).toBeInTheDocument();
  });

  it("renders batch header info", () => {
    renderSidebar();
    expect(screen.getByText("LOT-2026-001")).toBeInTheDocument();
    expect(screen.getByText("Parfum 100mL")).toBeInTheDocument();
  });

  it("highlights active step with aria-current", () => {
    renderSidebar({ activeStepId: 20 });
    const activeButton = screen.getByRole("button", {
      name: /Fichier de pesee/,
    });
    expect(activeButton).toHaveAttribute("aria-current", "step");
  });

  it("calls onStepSelect when a step is clicked", async () => {
    const user = userEvent.setup();
    const onStepSelect = vi.fn();
    renderSidebar({ onStepSelect });
    const stepButton = screen.getByRole("button", {
      name: /Execution conditionnement/,
    });
    await user.click(stepButton);
    expect(onStepSelect).toHaveBeenCalledWith(30);
  });

  it("renders step status badges", () => {
    renderSidebar();
    const badges = screen.getAllByRole("status");
    expect(badges.length).toBe(3);
  });
});
