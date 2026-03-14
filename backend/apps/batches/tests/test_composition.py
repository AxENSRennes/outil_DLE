from __future__ import annotations

from typing import Any

import pytest

from apps.batches.domain.composition import (
    CompositionError,
    CompositionResult,
    generate_repeated_controls,
)
from apps.batches.domain.occurrences import add_occurrence
from apps.batches.models import (
    Batch,
    BatchDocumentRepeatMode,
    BatchDocumentRequirement,
    BatchStep,
    BatchStepStatus,
)
from apps.sites.models import Site


@pytest.mark.django_db
class TestGenerateRepeatedControlsPMS:
    """Test composition with PMS + glitter context.

    Expected: gencod_control_uni2_uni3 is NOT applicable (mark_na),
    intermediate_leakage_pms_glitter IS applicable.
    """

    def test_creates_correct_step_count(self, batch_pms_glitter: Batch) -> None:
        result = generate_repeated_controls(batch_pms_glitter)
        assert isinstance(result, CompositionResult)
        # 9 step definitions in template:
        # single steps (5): fabrication_bulk, weighing, line_cleaning,
        #                    dossier_checklist, pre_qa_review = 5 steps
        # per_team (1): packaging_execution minRecords=1 = 1 step
        # per_box (2): finished_product_control minRecords=1 = 1,
        #              intermediate_leakage_pms_glitter minRecords=1 = 1
        # per_event (1): gencod_control_uni2_uni3 minRecords=3 = 3 (not applicable but mark_na)
        # Total = 5 + 1 + 1 + 1 + 3 = 11
        assert len(result.created_steps) == 11

    def test_single_steps_have_default_occurrence(self, batch_pms_glitter: Batch) -> None:
        generate_repeated_controls(batch_pms_glitter)
        fab = BatchStep.objects.get(batch=batch_pms_glitter, step_key="fabrication_bulk")
        assert fab.occurrence_key == "default"
        assert fab.occurrence_index == 1

    def test_per_team_step_occurrence_key(self, batch_pms_glitter: Batch) -> None:
        generate_repeated_controls(batch_pms_glitter)
        pkg = BatchStep.objects.get(batch=batch_pms_glitter, step_key="packaging_execution")
        assert pkg.occurrence_key == "packaging_execution_per_team_1"
        assert pkg.occurrence_index == 1

    def test_per_box_step_occurrence_key(self, batch_pms_glitter: Batch) -> None:
        generate_repeated_controls(batch_pms_glitter)
        fpc = BatchStep.objects.get(batch=batch_pms_glitter, step_key="finished_product_control")
        assert fpc.occurrence_key == "finished_product_control_per_box_1"
        assert fpc.occurrence_index == 1

    def test_per_event_creates_min_records(self, batch_pms_glitter: Batch) -> None:
        generate_repeated_controls(batch_pms_glitter)
        gencod_steps = BatchStep.objects.filter(
            batch=batch_pms_glitter, step_key="gencod_control_uni2_uni3"
        )
        assert gencod_steps.count() == 3
        indices = list(gencod_steps.values_list("occurrence_index", flat=True))
        assert sorted(indices) == [1, 2, 3]

    def test_gencod_not_applicable_for_pms(self, batch_pms_glitter: Batch) -> None:
        generate_repeated_controls(batch_pms_glitter)
        gencod = BatchStep.objects.filter(
            batch=batch_pms_glitter, step_key="gencod_control_uni2_uni3"
        ).first()
        assert gencod is not None
        assert gencod.is_applicable is False

    def test_intermediate_leakage_applicable_for_pms_glitter(
        self, batch_pms_glitter: Batch
    ) -> None:
        generate_repeated_controls(batch_pms_glitter)
        leakage = BatchStep.objects.get(
            batch=batch_pms_glitter, step_key="intermediate_leakage_pms_glitter"
        )
        assert leakage.is_applicable is True

    def test_sequence_order_respects_step_order(self, batch_pms_glitter: Batch) -> None:
        generate_repeated_controls(batch_pms_glitter)
        steps = list(BatchStep.objects.filter(batch=batch_pms_glitter).order_by("sequence_order"))
        step_keys_order = []
        for s in steps:
            if s.step_key not in step_keys_order:
                step_keys_order.append(s.step_key)

        expected_order = [
            "fabrication_bulk",
            "weighing",
            "line_cleaning_previous_run",
            "packaging_execution",
            "finished_product_control",
            "gencod_control_uni2_uni3",
            "intermediate_leakage_pms_glitter",
            "dossier_checklist_pre_qa",
            "pre_qa_review",
        ]
        assert step_keys_order == expected_order

    def test_occurrence_key_uniqueness_per_step_key(self, batch_pms_glitter: Batch) -> None:
        generate_repeated_controls(batch_pms_glitter)
        # Unique constraint is (batch, step_key, occurrence_key)
        tuples = list(
            BatchStep.objects.filter(batch=batch_pms_glitter).values_list(
                "step_key", "occurrence_key"
            )
        )
        assert len(tuples) == len(set(tuples))

    def test_document_requirements_created(self, batch_pms_glitter: Batch) -> None:
        result = generate_repeated_controls(batch_pms_glitter)
        doc_reqs = BatchDocumentRequirement.objects.filter(batch=batch_pms_glitter)
        assert doc_reqs.count() == 9  # all 9 steps (including not-applicable mark_na)
        assert result.document_requirements_created == 9

    def test_doc_req_repeat_mode_matches(self, batch_pms_glitter: Batch) -> None:
        generate_repeated_controls(batch_pms_glitter)
        fpc_doc = BatchDocumentRequirement.objects.get(
            batch=batch_pms_glitter, document_code="finished_product_control"
        )
        assert fpc_doc.repeat_mode == BatchDocumentRepeatMode.PER_BOX
        assert fpc_doc.expected_count == 1

        gencod_doc = BatchDocumentRequirement.objects.get(
            batch=batch_pms_glitter, document_code="gencod_control_uni2_uni3"
        )
        assert gencod_doc.repeat_mode == BatchDocumentRepeatMode.PER_EVENT
        assert gencod_doc.expected_count == 3

    def test_actual_count_matches_expected_after_composition(
        self, batch_pms_glitter: Batch
    ) -> None:
        generate_repeated_controls(batch_pms_glitter)
        for doc_req in BatchDocumentRequirement.objects.filter(batch=batch_pms_glitter):
            assert doc_req.actual_count == doc_req.expected_count

    def test_blocking_flags_from_template(self, batch_pms_glitter: Batch) -> None:
        generate_repeated_controls(batch_pms_glitter)
        fab = BatchStep.objects.get(batch=batch_pms_glitter, step_key="fabrication_bulk")
        assert fab.blocks_execution_progress is False
        assert fab.blocks_step_completion is True
        assert fab.blocks_signature is True
        assert fab.blocks_pre_qa_handoff is True

    def test_signature_state_from_template(self, batch_pms_glitter: Batch) -> None:
        generate_repeated_controls(batch_pms_glitter)
        fab = BatchStep.objects.get(batch=batch_pms_glitter, step_key="fabrication_bulk")
        assert fab.signature_state == "required"

        gencod = BatchStep.objects.filter(
            batch=batch_pms_glitter, step_key="gencod_control_uni2_uni3"
        ).first()
        assert gencod is not None
        assert gencod.signature_state == "not_required"

    def test_meta_json_contains_fields(self, batch_pms_glitter: Batch) -> None:
        generate_repeated_controls(batch_pms_glitter)
        fab = BatchStep.objects.get(batch=batch_pms_glitter, step_key="fabrication_bulk")
        assert "fields" in fab.meta_json
        assert len(fab.meta_json["fields"]) == 3


@pytest.mark.django_db
class TestGenerateRepeatedControlsUNI2:
    """Test composition with UNI2 context.

    Expected: gencod_control_uni2_uni3 IS applicable,
    intermediate_leakage_pms_glitter is NOT applicable (mark_na).
    """

    def test_gencod_applicable_for_uni2(self, batch_uni2: Batch) -> None:
        generate_repeated_controls(batch_uni2)
        gencod = BatchStep.objects.filter(
            batch=batch_uni2, step_key="gencod_control_uni2_uni3"
        ).first()
        assert gencod is not None
        assert gencod.is_applicable is True

    def test_intermediate_leakage_not_applicable_for_uni2(self, batch_uni2: Batch) -> None:
        generate_repeated_controls(batch_uni2)
        leakage = BatchStep.objects.get(
            batch=batch_uni2, step_key="intermediate_leakage_pms_glitter"
        )
        assert leakage.is_applicable is False

    def test_total_step_count_uni2(self, batch_uni2: Batch) -> None:
        generate_repeated_controls(batch_uni2)
        total = BatchStep.objects.filter(batch=batch_uni2).count()
        # Same total as PMS: 11 (all mark_na steps are still created)
        assert total == 11


@pytest.mark.django_db
class TestCompositionIdempotency:
    def test_recompose_does_not_duplicate_steps(self, batch_pms_glitter: Batch) -> None:
        generate_repeated_controls(batch_pms_glitter)
        first_count = BatchStep.objects.filter(batch=batch_pms_glitter).count()

        # Re-compose
        result = generate_repeated_controls(batch_pms_glitter)
        second_count = BatchStep.objects.filter(batch=batch_pms_glitter).count()

        assert first_count == second_count
        # Doc requirements already exist from first composition, so none are "created"
        assert result.document_requirements_created == 0

    def test_recompose_preserves_in_progress_steps(self, batch_pms_glitter: Batch) -> None:
        generate_repeated_controls(batch_pms_glitter)
        fab = BatchStep.objects.get(batch=batch_pms_glitter, step_key="fabrication_bulk")
        fab.status = BatchStepStatus.IN_PROGRESS
        fab.data_json = {"some": "data"}
        fab.save()

        # Re-compose
        generate_repeated_controls(batch_pms_glitter)

        fab.refresh_from_db()
        assert fab.status == BatchStepStatus.IN_PROGRESS
        assert fab.data_json == {"some": "data"}

    def test_recompose_doc_requirements_not_duplicated(self, batch_pms_glitter: Batch) -> None:
        generate_repeated_controls(batch_pms_glitter)
        first_count = BatchDocumentRequirement.objects.filter(batch=batch_pms_glitter).count()

        generate_repeated_controls(batch_pms_glitter)
        second_count = BatchDocumentRequirement.objects.filter(batch=batch_pms_glitter).count()

        assert first_count == second_count

    def test_recompose_preserves_added_not_started_occurrences(
        self, batch_pms_glitter: Batch
    ) -> None:
        generate_repeated_controls(batch_pms_glitter)
        add_occurrence(batch_pms_glitter, "finished_product_control")

        generate_repeated_controls(batch_pms_glitter)

        occurrences = list(
            BatchStep.objects.filter(
                batch=batch_pms_glitter,
                step_key="finished_product_control",
            )
            .order_by("occurrence_index")
            .values_list("occurrence_index", flat=True)
        )
        assert occurrences == [1, 2]

    def test_recompose_syncs_doc_requirement_counts_for_preserved_steps(
        self, batch_pms_glitter: Batch
    ) -> None:
        generate_repeated_controls(batch_pms_glitter)
        add_occurrence(batch_pms_glitter, "finished_product_control")

        first_step = BatchStep.objects.get(
            batch=batch_pms_glitter,
            step_key="finished_product_control",
            occurrence_index=1,
        )
        first_step.status = BatchStepStatus.IN_PROGRESS
        first_step.save(update_fields=["status", "updated_at"])

        generate_repeated_controls(batch_pms_glitter)

        doc_req = BatchDocumentRequirement.objects.get(
            batch=batch_pms_glitter,
            document_code="finished_product_control",
        )
        assert doc_req.expected_count == 2
        assert doc_req.actual_count == 2


@pytest.mark.django_db
class TestHiddenApplicability:
    """Test whenNotApplicable='hidden' skips step creation entirely."""

    @pytest.fixture()
    def batch_with_hidden_step(self, site: Site, user: Any) -> Batch:
        """Batch whose snapshot has one hidden step and one mark_na step."""
        snapshot = {
            "stepOrder": ["hidden_step", "mark_na_step"],
            "steps": {
                "hidden_step": {
                    "key": "hidden_step",
                    "title": "Hidden when not applicable",
                    "kind": "control",
                    "required": True,
                    "applicability": {
                        "machineCodes": ["NONEXISTENT"],
                        "whenNotApplicable": "hidden",
                    },
                    "repeatPolicy": {"mode": "single", "minRecords": 1, "maxRecords": 1},
                    "blockingPolicy": {
                        "blocksExecutionProgress": False,
                        "blocksStepCompletion": True,
                        "blocksSignature": False,
                        "blocksPreQaHandoff": True,
                    },
                    "fields": [],
                },
                "mark_na_step": {
                    "key": "mark_na_step",
                    "title": "Marked NA when not applicable",
                    "kind": "control",
                    "required": True,
                    "applicability": {
                        "machineCodes": ["NONEXISTENT"],
                        "whenNotApplicable": "mark_na",
                    },
                    "repeatPolicy": {"mode": "single", "minRecords": 1, "maxRecords": 1},
                    "blockingPolicy": {
                        "blocksExecutionProgress": False,
                        "blocksStepCompletion": True,
                        "blocksSignature": False,
                        "blocksPreQaHandoff": True,
                    },
                    "fields": [],
                },
            },
        }
        return Batch.objects.create(
            site=site,
            batch_number="LOT-HIDDEN-001",
            snapshot_json=snapshot,
            batch_context_json={"machine_code": "PMS"},
            created_by=user,
        )

    def test_hidden_step_not_created(self, batch_with_hidden_step: Batch) -> None:
        generate_repeated_controls(batch_with_hidden_step)
        assert not BatchStep.objects.filter(
            batch=batch_with_hidden_step, step_key="hidden_step"
        ).exists()

    def test_mark_na_step_created_not_applicable(self, batch_with_hidden_step: Batch) -> None:
        generate_repeated_controls(batch_with_hidden_step)
        step = BatchStep.objects.get(batch=batch_with_hidden_step, step_key="mark_na_step")
        assert step.is_applicable is False

    def test_no_doc_requirement_for_hidden_step(self, batch_with_hidden_step: Batch) -> None:
        generate_repeated_controls(batch_with_hidden_step)
        assert not BatchDocumentRequirement.objects.filter(
            batch=batch_with_hidden_step, document_code="hidden_step"
        ).exists()

    def test_doc_requirement_created_for_mark_na_step(self, batch_with_hidden_step: Batch) -> None:
        generate_repeated_controls(batch_with_hidden_step)
        doc_req = BatchDocumentRequirement.objects.get(
            batch=batch_with_hidden_step, document_code="mark_na_step"
        )
        assert doc_req.is_applicable is False


@pytest.mark.django_db
class TestCompositionErrors:
    def test_empty_snapshot_raises(self, batch_pms_glitter: Batch) -> None:
        batch_pms_glitter.snapshot_json = {}
        batch_pms_glitter.save()
        # Empty snapshot (no stepOrder/steps) produces no steps but doesn't error
        result = generate_repeated_controls(batch_pms_glitter)
        assert len(result.created_steps) == 0
        assert result.document_requirements_created == 0

    def test_missing_step_definition_raises(self, site: Site, user: Any) -> None:
        batch = Batch.objects.create(
            site=site,
            batch_number="LOT-BAD-SNAPSHOT",
            snapshot_json={"stepOrder": ["missing_step"], "steps": {}},
            created_by=user,
        )

        with pytest.raises(CompositionError, match="missing_step"):
            generate_repeated_controls(batch)

    def test_none_snapshot_raises(self, site: Site, user: Any) -> None:
        """Verify composition errors when snapshot_json is programmatically None."""

        batch = Batch(
            site=site,
            batch_number="LOT-NULL-SNAP",
            snapshot_json=None,
            created_by=user,
        )
        # Bypass DB save to test domain logic
        batch.pk = -1
        with pytest.raises(CompositionError, match="no template snapshot"):
            generate_repeated_controls(batch)
