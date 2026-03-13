from __future__ import annotations

from typing import TYPE_CHECKING, Any

from apps.batches.models import BatchStepStatus

if TYPE_CHECKING:
    from apps.batches.models import Batch, BatchStep


def get_batch_execution_payload(batch: Batch) -> dict[str, Any]:
    snapshot = batch.snapshot_json
    product = snapshot.get("product", {})
    steps = batch.steps.all()

    step_definitions = snapshot.get("steps", {})
    step_list: list[dict[str, Any]] = []
    current_step_id: int | None = None
    completed_count = 0
    applicable_count = 0

    for step in steps:
        step_def = step_definitions.get(step.step_key, {})
        sig_policy = step_def.get("signaturePolicy", {})

        step_list.append(
            {
                "id": step.id,
                "step_key": step.step_key,
                "sequence_order": step.sequence_order,
                "title": step.title,
                "kind": step_def.get("kind", ""),
                "status": step.status,
                "is_applicable": step.is_applicable,
                "signature_state": step.signature_state,
                "requires_signature": sig_policy.get("required", False),
            }
        )

        if step.is_applicable:
            applicable_count += 1
            if step.status in (BatchStepStatus.COMPLETE, BatchStepStatus.SIGNED):
                completed_count += 1
            elif current_step_id is None:
                current_step_id = step.id

    return {
        "id": batch.id,
        "batch_number": batch.batch_number,
        "status": batch.status,
        "product_name": product.get("productName", ""),
        "product_code": product.get("productCode", ""),
        "site": {
            "code": batch.site.code,
            "name": batch.site.name,
        },
        "template_name": snapshot.get("templateName", ""),
        "template_code": snapshot.get("templateCode", ""),
        "steps": step_list,
        "current_step_id": current_step_id,
        "progress": {
            "total": len(step_list),
            "completed": completed_count,
            "applicable": applicable_count,
        },
    }


def get_step_detail_payload(step: BatchStep) -> dict[str, Any]:
    batch = step.batch
    snapshot = batch.snapshot_json
    step_definitions = snapshot.get("steps", {})
    step_def = step_definitions.get(step.step_key, {})

    return {
        "id": step.id,
        "batch_id": batch.id,
        "step_key": step.step_key,
        "sequence_order": step.sequence_order,
        "title": step.title,
        "kind": step_def.get("kind", ""),
        "status": step.status,
        "is_applicable": step.is_applicable,
        "instructions": step_def.get("instructions", ""),
        "fields": step_def.get("fields", []),
        "signature_policy": step_def.get("signaturePolicy", {}),
        "blocking_policy": {
            "blocks_execution_progress": step.blocks_execution_progress,
            "blocks_step_completion": step.blocks_step_completion,
            "blocks_signature": step.blocks_signature,
            "blocks_pre_qa_handoff": step.blocks_pre_qa_handoff,
        },
        "data": step.data_json,
        "meta": step.meta_json,
    }
