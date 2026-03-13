import {
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/shared/ui/sidebar";
import type { StepSummary } from "../api/types";
import { StepStatusBadge } from "./StepStatusBadge";

interface StepSidebarItemProps {
  step: StepSummary;
  isActive: boolean;
  compact: boolean;
  onClick: (stepId: number) => void;
}

export function StepSidebarItem({
  step,
  isActive,
  compact,
  onClick,
}: StepSidebarItemProps) {
  return (
    <SidebarMenuItem>
      <SidebarMenuButton
        isActive={isActive}
        onClick={() => onClick(step.id)}
        aria-current={isActive ? "step" : undefined}
        tooltip={compact ? step.title : undefined}
        className="h-auto min-h-[44px] items-start py-2.5"
      >
        <span className="mt-0.5 shrink-0">
          <StepStatusBadge
            status={step.status}
            isApplicable={step.is_applicable}
            compact
          />
        </span>
        {!compact && (
          <span className="flex flex-col gap-0.5 min-w-0">
            <span className="text-sm leading-tight truncate">{step.title}</span>
            <span className="text-xs text-muted-foreground">
              Step {step.sequence_order}
            </span>
          </span>
        )}
      </SidebarMenuButton>
    </SidebarMenuItem>
  );
}
