from __future__ import annotations

import pytest

from apps.batches.domain.composition import generate_repeated_controls
from apps.batches.domain.occurrences import OccurrenceError, add_occurrence
from apps.batches.models import (
    Batch,
    BatchDocumentRequirement,
    BatchStep,
)


@pytest.mark.django_db
class TestAddOccurrence:
    def test_add_box_occurrence_succeeds(self, batch_pms_glitter: Batch) -> None:
        generate_repeated_controls(batch_pms_glitter)
        new_step = add_occurrence(batch_pms_glitter, "finished_product_control")
        assert new_step.occurrence_index == 2
        assert new_step.occurrence_key == "finished_product_control_per_box_2"
        assert new_step.step_key == "finished_product_control"

    def test_add_occurrence_increments_index(self, batch_pms_glitter: Batch) -> None:
        generate_repeated_controls(batch_pms_glitter)
        add_occurrence(batch_pms_glitter, "finished_product_control")
        step3 = add_occurrence(batch_pms_glitter, "finished_product_control")
        assert step3.occurrence_index == 3

    def test_add_occurrence_updates_doc_requirement(
        self, batch_pms_glitter: Batch
    ) -> None:
        generate_repeated_controls(batch_pms_glitter)
        doc_req = BatchDocumentRequirement.objects.get(
            batch=batch_pms_glitter, document_code="finished_product_control"
        )
        assert doc_req.expected_count == 1
        assert doc_req.actual_count == 1

        add_occurrence(batch_pms_glitter, "finished_product_control")
        doc_req.refresh_from_db()
        assert doc_req.expected_count == 2
        assert doc_req.actual_count == 2

    def test_add_occurrence_respects_max_records(
        self, batch_pms_glitter: Batch
    ) -> None:
        """gencod_control_uni2_uni3 has maxRecords=3, minRecords=3."""
        generate_repeated_controls(batch_pms_glitter)
        # Already at 3 records
        with pytest.raises(OccurrenceError, match="maximum of 3"):
            add_occurrence(batch_pms_glitter, "gencod_control_uni2_uni3")

    def test_add_occurrence_single_mode_raises(
        self, batch_pms_glitter: Batch
    ) -> None:
        generate_repeated_controls(batch_pms_glitter)
        with pytest.raises(OccurrenceError, match="single"):
            add_occurrence(batch_pms_glitter, "fabrication_bulk")

    def test_add_occurrence_unknown_step_raises(
        self, batch_pms_glitter: Batch
    ) -> None:
        with pytest.raises(OccurrenceError, match="not found"):
            add_occurrence(batch_pms_glitter, "nonexistent_step")

    def test_add_team_occurrence_succeeds(self, batch_pms_glitter: Batch) -> None:
        generate_repeated_controls(batch_pms_glitter)
        new_step = add_occurrence(batch_pms_glitter, "packaging_execution")
        assert new_step.occurrence_key == "packaging_execution_per_team_2"
        assert new_step.occurrence_index == 2

    def test_add_occurrence_preserves_applicability(
        self, batch_pms_glitter: Batch
    ) -> None:
        generate_repeated_controls(batch_pms_glitter)
        new_step = add_occurrence(
            batch_pms_glitter, "intermediate_leakage_pms_glitter"
        )
        assert new_step.is_applicable is True

    def test_occurrence_unique_constraint_enforced(
        self, batch_pms_glitter: Batch
    ) -> None:
        """Verify occurrence_key uniqueness after multiple adds."""
        generate_repeated_controls(batch_pms_glitter)
        add_occurrence(batch_pms_glitter, "finished_product_control")
        add_occurrence(batch_pms_glitter, "finished_product_control")
        all_keys = list(
            BatchStep.objects.filter(
                batch=batch_pms_glitter, step_key="finished_product_control"
            ).values_list("occurrence_key", flat=True)
        )
        assert len(all_keys) == len(set(all_keys))
