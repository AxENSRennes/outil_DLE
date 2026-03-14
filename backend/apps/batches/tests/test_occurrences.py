from __future__ import annotations

from typing import Any

import pytest
from django.db import IntegrityError

from apps.batches.domain.composition import generate_repeated_controls
from apps.batches.domain.occurrences import OccurrenceError, add_occurrence
from apps.batches.models import (
    Batch,
    BatchDocumentRequirement,
    BatchStep,
)
from apps.sites.models import Site


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

    def test_add_occurrence_updates_doc_requirement(self, batch_pms_glitter: Batch) -> None:
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

    def test_add_occurrence_respects_max_records(self, batch_uni2: Batch) -> None:
        """gencod_control_uni2_uni3 has maxRecords=3, minRecords=3."""
        generate_repeated_controls(batch_uni2)
        # Already at 3 records
        with pytest.raises(OccurrenceError, match="maximum of 3"):
            add_occurrence(batch_uni2, "gencod_control_uni2_uni3")

    def test_add_occurrence_single_mode_raises(self, batch_pms_glitter: Batch) -> None:
        generate_repeated_controls(batch_pms_glitter)
        with pytest.raises(OccurrenceError, match="single"):
            add_occurrence(batch_pms_glitter, "fabrication_bulk")

    def test_add_occurrence_unknown_step_raises(self, batch_pms_glitter: Batch) -> None:
        with pytest.raises(OccurrenceError, match="not found"):
            add_occurrence(batch_pms_glitter, "nonexistent_step")

    def test_add_occurrence_not_applicable_step_raises(self, batch_pms_glitter: Batch) -> None:
        generate_repeated_controls(batch_pms_glitter)
        with pytest.raises(OccurrenceError, match="not applicable"):
            add_occurrence(batch_pms_glitter, "gencod_control_uni2_uni3")

    def test_add_team_occurrence_succeeds(self, batch_pms_glitter: Batch) -> None:
        generate_repeated_controls(batch_pms_glitter)
        new_step = add_occurrence(batch_pms_glitter, "packaging_execution")
        assert new_step.occurrence_key == "packaging_execution_per_team_2"
        assert new_step.occurrence_index == 2

    def test_add_occurrence_preserves_applicability(self, batch_pms_glitter: Batch) -> None:
        generate_repeated_controls(batch_pms_glitter)
        new_step = add_occurrence(batch_pms_glitter, "intermediate_leakage_pms_glitter")
        assert new_step.is_applicable is True

    def test_occurrence_unique_constraint_enforced(self, batch_pms_glitter: Batch) -> None:
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

    @pytest.fixture()
    def batch_with_hidden_repeated_step(self, site: Site, user: Any) -> Batch:
        snapshot = {
            "stepOrder": ["hidden_repeated_step"],
            "steps": {
                "hidden_repeated_step": {
                    "key": "hidden_repeated_step",
                    "title": "Hidden repeated step",
                    "kind": "in_process_control",
                    "required": True,
                    "applicability": {
                        "machineCodes": ["UNI2"],
                        "whenNotApplicable": "hidden",
                    },
                    "repeatPolicy": {
                        "mode": "per_box",
                        "minRecords": 1,
                    },
                    "blockingPolicy": {
                        "blocksExecutionProgress": False,
                        "blocksStepCompletion": True,
                        "blocksSignature": False,
                        "blocksPreQaHandoff": True,
                    },
                    "signaturePolicy": {
                        "required": False,
                        "meaning": "performed_by",
                    },
                    "fields": [],
                }
            },
        }
        return Batch.objects.create(
            site=site,
            batch_number="LOT-HIDDEN-OCC-001",
            snapshot_json=snapshot,
            batch_context_json={"machine_code": "PMS"},
            created_by=user,
        )

    def test_add_occurrence_hidden_step_raises(
        self, batch_with_hidden_repeated_step: Batch
    ) -> None:
        with pytest.raises(OccurrenceError, match="hidden"):
            add_occurrence(batch_with_hidden_repeated_step, "hidden_repeated_step")

    def test_add_occurrence_conflict_raises_controlled_error(
        self,
        batch_pms_glitter: Batch,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        generate_repeated_controls(batch_pms_glitter)

        def raise_integrity_error(*args: object, **kwargs: object) -> BatchStep:
            raise IntegrityError("uniq_batch_step_occurrence")

        monkeypatch.setattr(BatchStep.objects, "create", raise_integrity_error)

        with pytest.raises(OccurrenceError, match="concurrently") as exc_info:
            add_occurrence(batch_pms_glitter, "finished_product_control")

        assert exc_info.value.status_code == 409
        assert exc_info.value.code == "occurrence_conflict"

    def test_add_occurrence_without_composition_raises(self, batch_pms_glitter: Batch) -> None:
        """Calling add_occurrence before generate_repeated_controls must fail."""
        with pytest.raises(OccurrenceError, match="composition") as exc_info:
            add_occurrence(batch_pms_glitter, "finished_product_control")
        assert exc_info.value.code == "composition_required"

    def test_add_occurrence_deleted_doc_requirement_raises(self, batch_pms_glitter: Batch) -> None:
        """If doc requirement is deleted after composition, add_occurrence must fail."""
        generate_repeated_controls(batch_pms_glitter)
        BatchDocumentRequirement.objects.filter(
            batch=batch_pms_glitter, document_code="finished_product_control"
        ).delete()
        with pytest.raises(OccurrenceError, match="composition") as exc_info:
            add_occurrence(batch_pms_glitter, "finished_product_control")
        assert exc_info.value.code == "composition_required"
