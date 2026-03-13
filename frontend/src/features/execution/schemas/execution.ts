import { z } from "zod";

export const siteBriefSchema = z.object({
  code: z.string(),
  name: z.string(),
});

export const stepSummarySchema = z.object({
  id: z.number(),
  step_key: z.string(),
  sequence_order: z.number(),
  title: z.string(),
  kind: z.string(),
  status: z.enum(["not_started", "in_progress", "complete", "signed"]),
  is_applicable: z.boolean(),
  signature_state: z.enum(["not_required", "required", "signed"]),
  requires_signature: z.boolean(),
});

export const progressSchema = z.object({
  total: z.number(),
  completed: z.number(),
  applicable: z.number(),
});

export const batchExecutionSchema = z.object({
  id: z.number(),
  batch_number: z.string(),
  status: z.string(),
  product_name: z.string(),
  product_code: z.string(),
  site: siteBriefSchema,
  template_name: z.string(),
  template_code: z.string(),
  steps: z.array(stepSummarySchema),
  current_step_id: z.number().nullable(),
  progress: progressSchema,
});

export const fieldDefinitionSchema = z.object({
  key: z.string(),
  type: z.string(),
  label: z.string(),
  required: z.boolean().optional(),
  options: z
    .array(z.object({ value: z.string(), label: z.string() }))
    .optional(),
  unit: z.string().optional(),
  validation: z.record(z.string(), z.unknown()).optional(),
});

export const signaturePolicySchema = z.object({
  required: z.boolean().default(false),
  meaning: z.string().default(""),
});

export const blockingPolicySchema = z.object({
  blocks_execution_progress: z.boolean(),
  blocks_step_completion: z.boolean(),
  blocks_signature: z.boolean(),
  blocks_pre_qa_handoff: z.boolean(),
});

export const stepDetailSchema = z.object({
  id: z.number(),
  batch_id: z.number(),
  step_key: z.string(),
  sequence_order: z.number(),
  title: z.string(),
  kind: z.string(),
  status: z.enum(["not_started", "in_progress", "complete", "signed"]),
  is_applicable: z.boolean(),
  instructions: z.string(),
  fields: z.array(fieldDefinitionSchema),
  signature_policy: signaturePolicySchema.default({ required: false, meaning: "" }),
  blocking_policy: blockingPolicySchema,
  data: z.record(z.string(), z.unknown()),
  meta: z.record(z.string(), z.unknown()),
});
