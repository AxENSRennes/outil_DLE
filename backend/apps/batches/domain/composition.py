from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from django.db import transaction

from apps.batches.domain.template_rules import (
    ResolvedStepDefinition,
    resolve_document_repeat_mode,
    resolve_step_definition,
)
from apps.batches.models import (
    Batch,
    BatchDocumentRequirement,
    BatchStep,
    BatchStepStatus,
)


class CompositionError(Exception):
    def __init__(
        self,
        detail: str,
        *,
        code: str = "composition_error",
        status_code: int = 400,
    ) -> None:
        super().__init__(detail)
        self.detail = detail
        self.code = code
        self.status_code = status_code


@dataclass(frozen=True)
class CompositionResult:
    created_steps: list[BatchStep]
    document_requirements_created: int


def _sync_document_requirement(
    batch: Batch,
    *,
    resolved_step: ResolvedStepDefinition,
    actual_count: int,
    is_applicable: bool | None = None,
    applicability_basis: dict[str, object] | None = None,
) -> bool:
    """Sync a BatchDocumentRequirement record. Returns True if created, False if updated."""
    _, created = BatchDocumentRequirement.objects.update_or_create(
        batch=batch,
        document_code=resolved_step.step_key,
        defaults={
            "title": resolved_step.title,
            "source_step_key": resolved_step.step_key,
            "is_required": resolved_step.is_required,
            "is_applicable": (
                resolved_step.is_applicable if is_applicable is None else is_applicable
            ),
            "repeat_mode": resolve_document_repeat_mode(resolved_step.repeat_mode),
            "expected_count": actual_count,
            "actual_count": actual_count,
            "applicability_basis_json": (
                resolved_step.applicability_basis
                if applicability_basis is None
                else applicability_basis
            ),
        },
    )
    return created


@transaction.atomic
def generate_repeated_controls(batch: Batch) -> CompositionResult:
    """Generate BatchStep and BatchDocumentRequirement records from the frozen
    template snapshot stored in batch.snapshot_json.

    This function is idempotent: it only creates steps with NOT_STARTED status
    and skips step_keys that already have non-NOT_STARTED records.
    """
    snapshot = batch.snapshot_json
    if snapshot is None:
        raise CompositionError("Batch has no template snapshot.")

    step_order: list[str] = snapshot.get("stepOrder", [])
    batch_context = batch.batch_context_json or {}

    # Prefetch all existing steps in one query (avoids N+1 per step_key)
    all_existing = list(BatchStep.objects.filter(batch=batch).order_by("occurrence_index"))
    steps_by_key: dict[str, list[BatchStep]] = defaultdict(list)
    for step in all_existing:
        steps_by_key[step.step_key].append(step)

    created_steps: list[BatchStep] = []
    doc_reqs_created = 0

    for position, step_key in enumerate(step_order):
        try:
            resolved_step = resolve_step_definition(snapshot, batch_context, step_key)
        except ValueError as exc:
            raise CompositionError(str(exc)) from exc
        except KeyError:
            continue

        existing_for_key = steps_by_key.get(step_key, [])

        # Idempotency check: if non-NOT_STARTED steps exist for this step_key, skip
        non_initial = [s for s in existing_for_key if s.status != BatchStepStatus.NOT_STARTED]
        if non_initial:
            reference_step = existing_for_key[0]  # sorted by occurrence_index
            created = _sync_document_requirement(
                batch,
                resolved_step=resolved_step,
                actual_count=len(existing_for_key),
                is_applicable=reference_step.is_applicable,
                applicability_basis=reference_step.applicability_basis_json,
            )
            if created:
                doc_reqs_created += 1
            continue

        if resolved_step.is_hidden:
            not_started_pks = [
                s.pk for s in existing_for_key if s.status == BatchStepStatus.NOT_STARTED
            ]
            if not_started_pks:
                BatchStep.objects.filter(pk__in=not_started_pks).delete()
            BatchDocumentRequirement.objects.filter(
                batch=batch,
                document_code=step_key,
            ).delete()
            continue

        # Delete existing NOT_STARTED steps for this step_key (re-composition)
        not_started_pks = [
            s.pk for s in existing_for_key if s.status == BatchStepStatus.NOT_STARTED
        ]
        if not_started_pks:
            BatchStep.objects.filter(pk__in=not_started_pks).delete()

        record_count = resolved_step.initial_record_count
        step_records: list[BatchStep] = []

        for idx in range(1, record_count + 1):
            occurrence_key = (
                "default"
                if resolved_step.repeat_mode == "single"
                else f"{step_key}_{resolved_step.repeat_mode}_{idx}"
            )

            sequence = position * 1000 + idx

            step_record = BatchStep(
                batch=batch,
                step_key=step_key,
                occurrence_key=occurrence_key,
                occurrence_index=idx,
                title=resolved_step.title,
                sequence_order=sequence,
                source_document_code=step_key,
                is_applicable=resolved_step.is_applicable,
                applicability_basis_json=resolved_step.applicability_basis,
                status=BatchStepStatus.NOT_STARTED,
                review_state="none",
                signature_state=resolved_step.signature_state,
                blocks_execution_progress=resolved_step.blocks_execution_progress,
                blocks_step_completion=resolved_step.blocks_step_completion,
                blocks_signature=resolved_step.blocks_signature,
                blocks_pre_qa_handoff=resolved_step.blocks_pre_qa_handoff,
                data_json={},
                meta_json={"fields": resolved_step.fields},
            )
            step_records.append(step_record)

        BatchStep.objects.bulk_create(step_records)
        created_steps.extend(step_records)

        created = _sync_document_requirement(
            batch,
            resolved_step=resolved_step,
            actual_count=len(step_records),
        )
        if created:
            doc_reqs_created += 1

    return CompositionResult(
        created_steps=created_steps,
        document_requirements_created=doc_reqs_created,
    )
