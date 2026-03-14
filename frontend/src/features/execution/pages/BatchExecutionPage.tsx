import { useParams } from "react-router-dom";

import { BatchExecutionShell } from "../components/BatchExecutionShell";

export function BatchExecutionPage() {
  const { batchId } = useParams<{ batchId: string }>();
  const numericId = Number(batchId);

  if (!batchId || Number.isNaN(numericId) || numericId <= 0) {
    return (
      <div className="flex h-screen items-center justify-center text-destructive">
        Invalid batch ID.
      </div>
    );
  }

  return <BatchExecutionShell batchId={numericId} />;
}
