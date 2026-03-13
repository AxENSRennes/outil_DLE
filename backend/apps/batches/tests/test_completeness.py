from __future__ import annotations

import pytest

from apps.batches.domain.composition import generate_repeated_controls
from apps.batches.domain.occurrences import add_occurrence
from apps.batches.models import Batch, BatchStep, BatchStepStatus
from apps.batches.selectors.completeness import (
    get_document_requirement_completeness,
    get_occurrence_details,
    get_step_completeness_by_group,
)


@pytest.mark.django_db
class TestStepCompletenessByGroup:
    def test_all_not_started_returns_zero_completed(
        self, batch_pms_glitter: Batch
    ) -> None:
        generate_repeated_controls(batch_pms_glitter)
        results = get_step_completeness_by_group(batch_pms_glitter)
        for group in results:
            assert group["completed"] == 0

    def test_mixed_completion_counts(self, batch_pms_glitter: Batch) -> None:
        generate_repeated_controls(batch_pms_glitter)
        # Add more box occurrences
        for _ in range(4):
            add_occurrence(batch_pms_glitter, "finished_product_control")

        # Complete 3 of 5
        fpc_steps = BatchStep.objects.filter(
            batch=batch_pms_glitter, step_key="finished_product_control"
        ).order_by("occurrence_index")[:3]
        for step in fpc_steps:
            step.status = BatchStepStatus.COMPLETED
            step.save()

        results = get_step_completeness_by_group(batch_pms_glitter)
        fpc_group = next(
            r for r in results if r["step_key"] == "finished_product_control"
        )
        assert fpc_group["total"] == 5
        assert fpc_group["completed"] == 3
        assert fpc_group["incomplete"] == 2

    def test_non_applicable_excluded(self, batch_pms_glitter: Batch) -> None:
        generate_repeated_controls(batch_pms_glitter)
        # gencod_control_uni2_uni3 is not applicable for PMS
        results = get_step_completeness_by_group(batch_pms_glitter)
        gencod_group = [
            r for r in results if r["step_key"] == "gencod_control_uni2_uni3"
        ]
        # Non-applicable steps should NOT appear in completeness (filtered out)
        assert len(gencod_group) == 0


@pytest.mark.django_db
class TestDocumentRequirementCompleteness:
    def test_initial_completeness(self, batch_pms_glitter: Batch) -> None:
        generate_repeated_controls(batch_pms_glitter)
        results = get_document_requirement_completeness(batch_pms_glitter)
        fab_doc = next(
            r for r in results if r["document_code"] == "fabrication_bulk"
        )
        assert fab_doc["expected_count"] == 1
        assert fab_doc["actual_completed"] == 0
        assert fab_doc["is_complete"] is False

    def test_completed_doc_requirement(self, batch_pms_glitter: Batch) -> None:
        generate_repeated_controls(batch_pms_glitter)
        fab = BatchStep.objects.get(
            batch=batch_pms_glitter, step_key="fabrication_bulk"
        )
        fab.status = BatchStepStatus.COMPLETED
        fab.save()

        results = get_document_requirement_completeness(batch_pms_glitter)
        fab_doc = next(
            r for r in results if r["document_code"] == "fabrication_bulk"
        )
        assert fab_doc["actual_completed"] == 1
        assert fab_doc["is_complete"] is True

    def test_non_applicable_doc_not_complete(
        self, batch_pms_glitter: Batch
    ) -> None:
        generate_repeated_controls(batch_pms_glitter)
        results = get_document_requirement_completeness(batch_pms_glitter)
        gencod_doc = next(
            r for r in results if r["document_code"] == "gencod_control_uni2_uni3"
        )
        assert gencod_doc["is_applicable"] is False
        assert gencod_doc["is_complete"] is False


    def test_flagged_status_counts_as_completed(
        self, batch_pms_glitter: Batch
    ) -> None:
        generate_repeated_controls(batch_pms_glitter)
        fab = BatchStep.objects.get(
            batch=batch_pms_glitter, step_key="fabrication_bulk"
        )
        fab.status = BatchStepStatus.FLAGGED
        fab.save()

        results = get_document_requirement_completeness(batch_pms_glitter)
        fab_doc = next(
            r for r in results if r["document_code"] == "fabrication_bulk"
        )
        assert fab_doc["actual_completed"] == 1
        assert fab_doc["is_complete"] is True

    def test_under_review_status_counts_as_completed(
        self, batch_pms_glitter: Batch
    ) -> None:
        generate_repeated_controls(batch_pms_glitter)
        fab = BatchStep.objects.get(
            batch=batch_pms_glitter, step_key="fabrication_bulk"
        )
        fab.status = BatchStepStatus.UNDER_REVIEW
        fab.save()

        results = get_document_requirement_completeness(batch_pms_glitter)
        fab_doc = next(
            r for r in results if r["document_code"] == "fabrication_bulk"
        )
        assert fab_doc["actual_completed"] == 1
        assert fab_doc["is_complete"] is True


@pytest.mark.django_db
class TestOccurrenceDetails:
    def test_returns_all_occurrences(self, batch_pms_glitter: Batch) -> None:
        generate_repeated_controls(batch_pms_glitter)
        details = get_occurrence_details(
            batch_pms_glitter, "gencod_control_uni2_uni3"
        )
        assert len(details) == 3
        indices = [d["occurrence_index"] for d in details]
        assert indices == [1, 2, 3]

    def test_single_step_occurrence(self, batch_pms_glitter: Batch) -> None:
        generate_repeated_controls(batch_pms_glitter)
        details = get_occurrence_details(batch_pms_glitter, "fabrication_bulk")
        assert len(details) == 1
        assert details[0]["occurrence_key"] == "default"
