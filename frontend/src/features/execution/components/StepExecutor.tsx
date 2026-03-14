import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/shared/ui/card";
import { Badge } from "@/shared/ui/badge";
import { Skeleton } from "@/shared/ui/skeleton";
import { Separator } from "@/shared/ui/separator";
import { useStepDetail } from "../api/queries";
import { StepStatusBadge } from "./StepStatusBadge";
import { StepFieldList } from "./StepFieldList";

interface StepExecutorProps {
  stepId: number | null;
}

export function StepExecutor({ stepId }: StepExecutorProps) {
  const { data: step, isLoading, error } = useStepDetail(stepId);

  if (stepId == null) {
    return (
      <div className="flex items-center justify-center h-full text-muted-foreground">
        All steps complete.
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="space-y-4 p-6">
        <Skeleton className="h-8 w-2/3" />
        <Skeleton className="h-4 w-1/2" />
        <Skeleton className="h-32 w-full" />
      </div>
    );
  }

  if (error || !step) {
    return (
      <div className="flex items-center justify-center h-full text-destructive">
        Failed to load step details.
      </div>
    );
  }

  return (
    <article aria-live="polite" className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <CardTitle className="text-xl">{step.title}</CardTitle>
            <StepStatusBadge
              status={step.status}
              isApplicable={step.is_applicable}
            />
          </div>
          <CardDescription className="flex items-center gap-2">
            <Badge variant="outline">{step.kind}</Badge>
            <span>Step {step.sequence_order}</span>
          </CardDescription>
        </CardHeader>
        {step.instructions && (
          <CardContent>
            <p className="text-sm text-muted-foreground">
              {step.instructions}
            </p>
          </CardContent>
        )}
      </Card>

      <Separator />

      <section>
        <h2 className="text-base font-semibold mb-4">Field Definitions</h2>
        <StepFieldList fields={step.fields} />
      </section>
    </article>
  );
}
