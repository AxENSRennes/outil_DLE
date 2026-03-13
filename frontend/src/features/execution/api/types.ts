export type StepStatus = "not_started" | "in_progress" | "complete" | "signed";

export type SignatureState = "not_required" | "required" | "signed";

export interface SiteBrief {
  code: string;
  name: string;
}

export interface StepSummary {
  id: number;
  step_key: string;
  sequence_order: number;
  title: string;
  kind: string;
  status: StepStatus;
  is_applicable: boolean;
  signature_state: SignatureState;
  requires_signature: boolean;
}

export interface Progress {
  total: number;
  completed: number;
  applicable: number;
}

export interface BatchExecution {
  id: number;
  batch_number: string;
  status: string;
  product_name: string;
  product_code: string;
  site: SiteBrief;
  template_name: string;
  template_code: string;
  steps: StepSummary[];
  current_step_id: number | null;
  progress: Progress;
}

export interface BlockingPolicy {
  blocks_execution_progress: boolean;
  blocks_step_completion: boolean;
  blocks_signature: boolean;
  blocks_pre_qa_handoff: boolean;
}

export interface FieldDefinition {
  key: string;
  type: string;
  label: string;
  required?: boolean;
  options?: Array<{ value: string; label: string }>;
  unit?: string;
  validation?: Record<string, unknown>;
}

export interface SignaturePolicy {
  required: boolean;
  meaning: string;
}

export interface StepDetail {
  id: number;
  batch_id: number;
  step_key: string;
  sequence_order: number;
  title: string;
  kind: string;
  status: StepStatus;
  is_applicable: boolean;
  instructions: string;
  fields: FieldDefinition[];
  signature_policy: SignaturePolicy;
  blocking_policy: BlockingPolicy;
  data: Record<string, unknown>;
  meta: Record<string, unknown>;
}
