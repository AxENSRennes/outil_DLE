import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/shared/ui/card";
import { Badge } from "@/shared/ui/badge";
import type { FieldDefinition } from "../api/types";

interface StepFieldListProps {
  fields: FieldDefinition[];
}

export function StepFieldList({ fields }: StepFieldListProps) {
  if (fields.length === 0) {
    return (
      <p className="text-sm text-muted-foreground italic">
        No fields defined for this step.
      </p>
    );
  }

  return (
    <div className="space-y-4">
      {fields.map((field) => (
        <Card key={field.key} className="shadow-none">
          <CardHeader className="py-3 px-4">
            <div className="flex items-center gap-2">
              <CardTitle className="text-sm font-medium">
                {field.label}
              </CardTitle>
              <Badge variant="outline" className="text-xs font-normal">
                {field.type}
              </Badge>
              {field.required && (
                <Badge variant="secondary" className="text-xs font-normal">
                  Required
                </Badge>
              )}
            </div>
          </CardHeader>
          {field.options && field.options.length > 0 && (
            <CardContent className="px-4 pb-3 pt-0">
              <span className="text-xs text-muted-foreground">
                Options:{" "}
                {field.options.map((o) => o.label).join(", ")}
              </span>
            </CardContent>
          )}
        </Card>
      ))}
    </div>
  );
}
