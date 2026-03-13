import { useCallback, useRef, useEffect } from "react";

import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  useSidebar,
} from "@/shared/ui/sidebar";
import { ScrollArea } from "@/shared/ui/scroll-area";
import type { BatchExecution } from "../api/types";
import { StepSidebarItem } from "./StepSidebarItem";

interface StepSidebarProps {
  batch: BatchExecution;
  activeStepId: number | null;
  onStepSelect: (stepId: number) => void;
}

export function StepSidebar({
  batch,
  activeStepId,
  onStepSelect,
}: StepSidebarProps) {
  const { state } = useSidebar();
  const compact = state === "collapsed";
  const listRef = useRef<HTMLUListElement>(null);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (!listRef.current) return;
      const items = Array.from(
        listRef.current.querySelectorAll<HTMLButtonElement>(
          "[role='menuitem'], button"
        )
      );
      const idx = items.findIndex((el) => el === document.activeElement);
      if (idx === -1) return;

      if (e.key === "ArrowDown" && idx < items.length - 1) {
        e.preventDefault();
        items[idx + 1].focus();
      } else if (e.key === "ArrowUp" && idx > 0) {
        e.preventDefault();
        items[idx - 1].focus();
      } else if (e.key === "Enter") {
        e.preventDefault();
        items[idx].click();
      }
    },
    []
  );

  useEffect(() => {
    if (!listRef.current || activeStepId == null) return;
    const active = listRef.current.querySelector('[aria-current="step"]');
    active?.scrollIntoView({ block: "nearest" });
  }, [activeStepId]);

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader className="border-b px-4 py-3">
        {!compact && (
          <div className="flex flex-col gap-1">
            <span className="text-sm font-semibold truncate">
              {batch.batch_number}
            </span>
            <span className="text-xs text-muted-foreground truncate">
              {batch.product_name}
            </span>
            <span className="text-xs text-muted-foreground">
              {batch.progress.completed}/{batch.progress.applicable} complete
            </span>
          </div>
        )}
      </SidebarHeader>
      <SidebarContent>
        <ScrollArea className="h-full">
          <SidebarGroup>
            <SidebarGroupLabel>Execution Steps</SidebarGroupLabel>
            <SidebarMenu ref={listRef} onKeyDown={handleKeyDown}>
              {batch.steps.map((step) => (
                <StepSidebarItem
                  key={step.id}
                  step={step}
                  isActive={step.id === activeStepId}
                  compact={compact}
                  onClick={onStepSelect}
                />
              ))}
            </SidebarMenu>
          </SidebarGroup>
        </ScrollArea>
      </SidebarContent>
    </Sidebar>
  );
}
