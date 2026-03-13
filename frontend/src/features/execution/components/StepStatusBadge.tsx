import { Circle, CheckCircle, Lock, Minus, Loader } from "lucide-react";

import { Badge } from "@/shared/ui/badge";
import { cn } from "@/shared/lib/cn";
import type { StepStatus } from "../api/types";

interface StepStatusBadgeProps {
  status: StepStatus;
  isApplicable: boolean;
  compact?: boolean;
}

const STATUS_CONFIG: Record<
  StepStatus | "na",
  { icon: typeof Circle; label: string; className: string }
> = {
  not_started: {
    icon: Circle,
    label: "Not Started",
    className: "border-gray-300 bg-gray-50 text-gray-600",
  },
  in_progress: {
    icon: Loader,
    label: "In Progress",
    className: "border-blue-300 bg-blue-50 text-blue-700",
  },
  complete: {
    icon: CheckCircle,
    label: "Complete",
    className: "border-green-300 bg-green-50 text-green-700",
  },
  signed: {
    icon: Lock,
    label: "Signed",
    className: "border-green-300 bg-green-50 text-green-700",
  },
  na: {
    icon: Minus,
    label: "N/A",
    className: "border-gray-200 bg-gray-50 text-gray-400",
  },
};

export function StepStatusBadge({
  status,
  isApplicable,
  compact = false,
}: StepStatusBadgeProps) {
  const config = isApplicable ? STATUS_CONFIG[status] : STATUS_CONFIG.na;
  const Icon = config.icon;

  return (
    <Badge
      variant="outline"
      className={cn("gap-1.5 font-medium", config.className)}
      role="status"
      aria-label={config.label}
    >
      <Icon
        className={cn(
          "size-3.5 shrink-0",
          status === "in_progress" && isApplicable && "animate-pulse"
        )}
        aria-hidden="true"
      />
      {!compact && <span>{config.label}</span>}
    </Badge>
  );
}
