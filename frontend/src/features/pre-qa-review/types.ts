export interface StepSummary {
  total: number;
  not_started: number;
  in_progress: number;
  complete: number;
  signed: number;
}

export interface FlagCounts {
  missing_required_data: number;
  missing_required_signatures: number;
  changed_since_review: number;
  changed_since_signature: number;
  open_exceptions: number;
  review_required: number;
  blocking_open_exceptions: number;
}

export interface ChecklistSummary {
  expected_documents: number;
  present_documents: number;
  missing_documents: string[];
}

export interface FlaggedStep {
  step_id: number;
  step_reference: string;
  step_status: string;
  flags: string[];
  severity: "green" | "amber" | "red";
}

export interface ReviewSummary {
  batch_id: number;
  batch_number: string;
  batch_status: string;
  severity: "green" | "amber" | "red";
  step_summary: StepSummary;
  flags: FlagCounts;
  checklist: ChecklistSummary;
  flagged_steps: FlaggedStep[];
}

export interface PreQaReviewConfirmation {
  batch_id: number;
  batch_number: string;
  batch_status: string;
  confirmed_at: string;
  reviewer_note: string;
}

export interface MarkStepReviewedResponse {
  step_id: number;
  step_reference: string;
  review_status: string;
  flags_cleared: string[];
  batch_status: string;
}
