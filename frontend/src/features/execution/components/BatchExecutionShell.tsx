import { useState, useCallback, useEffect } from "react";

import { SidebarInset, SidebarProvider } from "@/shared/ui/sidebar";
import { Skeleton } from "@/shared/ui/skeleton";
import { useBatchExecution } from "../api/queries";
import { BatchHeader } from "./BatchHeader";
import { StepSidebar } from "./StepSidebar";
import { StepExecutor } from "./StepExecutor";

interface BatchExecutionShellProps {
  batchId: number;
}

export function BatchExecutionShell({ batchId }: BatchExecutionShellProps) {
  const { data: batch, isLoading, error } = useBatchExecution(batchId);
  const [activeStepId, setActiveStepId] = useState<number | null>(null);

  useEffect(() => {
    if (batch && activeStepId == null) {
      setActiveStepId(batch.current_step_id);
    }
  }, [batch, activeStepId]);

  const handleStepSelect = useCallback((stepId: number) => {
    setActiveStepId(stepId);
  }, []);

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="space-y-4 w-64">
          <Skeleton className="h-6 w-full" />
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-4 w-1/2" />
        </div>
      </div>
    );
  }

  if (error || !batch) {
    return (
      <div className="flex h-screen items-center justify-center text-destructive">
        Failed to load batch execution.
      </div>
    );
  }

  return (
    <SidebarProvider>
      <StepSidebar
        batch={batch}
        activeStepId={activeStepId}
        onStepSelect={handleStepSelect}
      />
      <SidebarInset>
        <BatchHeader batch={batch} />
        <main className="flex-1 overflow-auto">
          <div className="mx-auto max-w-[720px] p-6">
            <StepExecutor stepId={activeStepId} />
          </div>
        </main>
      </SidebarInset>
    </SidebarProvider>
  );
}
