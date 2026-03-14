from __future__ import annotations

from typing import Any

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from apps.batches.models import (
    Batch,
    BatchDocumentRepeatMode,
    BatchDocumentRequirement,
    BatchDocumentStatus,
    BatchStatus,
    BatchStep,
    BatchStepStatus,
    ReviewState,
    SignatureState,
    StepReviewState,
    StepSignatureState,
)
from apps.sites.models import Site

User = get_user_model()


@pytest.fixture()
def site(db: None) -> Site:
    return Site.objects.create(code="chr", name="Chateau-Renard")


@pytest.fixture()
def user(db: None) -> Any:
    return User.objects.create_user(username="operator1", password="testpass")


@pytest.fixture()
def batch(site: Site, user: Any) -> Batch:
    return Batch.objects.create(
        site=site,
        batch_number="LOT-2026-001",
        snapshot_json={"schemaVersion": "v1", "steps": {}},
        created_by=user,
    )


@pytest.mark.django_db
class TestBatchModel:
    def test_create_batch_with_defaults(self, site: Site, user: Any) -> None:
        batch = Batch.objects.create(
            site=site,
            batch_number="LOT-001",
            snapshot_json={"steps": {}},
            created_by=user,
        )
        assert batch.status == BatchStatus.DRAFT
        assert batch.review_state == ReviewState.NONE
        assert batch.signature_state == SignatureState.NONE
        assert batch.batch_context_json == {}
        assert batch.lot_size_target is None
        assert batch.assigned_to is None

    def test_batch_str(self, batch: Batch) -> None:
        assert str(batch) == "LOT-2026-001"

    def test_unique_batch_number(self, site: Site, user: Any) -> None:
        Batch.objects.create(
            site=site,
            batch_number="LOT-UNIQUE",
            snapshot_json={},
            created_by=user,
        )
        with pytest.raises(IntegrityError):
            Batch.objects.create(
                site=site,
                batch_number="LOT-UNIQUE",
                snapshot_json={},
                created_by=user,
            )


@pytest.mark.django_db
class TestBatchStepModel:
    def test_create_step_with_defaults(self, batch: Batch) -> None:
        step = BatchStep.objects.create(
            batch=batch,
            step_key="fabrication_bulk",
            title="Fabrication bulk",
            sequence_order=1,
        )
        assert step.occurrence_key == "default"
        assert step.occurrence_index == 1
        assert step.status == BatchStepStatus.NOT_STARTED
        assert step.review_state == StepReviewState.NONE
        assert step.signature_state == StepSignatureState.NOT_REQUIRED
        assert step.is_applicable is True
        assert step.blocks_execution_progress is False
        assert step.blocks_step_completion is True
        assert step.blocks_signature is False
        assert step.blocks_pre_qa_handoff is True
        assert step.data_json == {}
        assert step.meta_json == {}

    def test_step_str(self, batch: Batch) -> None:
        step = BatchStep.objects.create(
            batch=batch,
            step_key="weighing",
            occurrence_key="default",
            title="Weighing",
            sequence_order=2,
        )
        assert str(step) == "LOT-2026-001 / weighing / default"

    def test_unique_constraint_batch_step_occurrence(self, batch: Batch) -> None:
        BatchStep.objects.create(
            batch=batch,
            step_key="ctrl",
            occurrence_key="ctrl_per_box_1",
            title="Control 1",
            sequence_order=1,
        )
        with pytest.raises(IntegrityError):
            BatchStep.objects.create(
                batch=batch,
                step_key="ctrl",
                occurrence_key="ctrl_per_box_1",
                title="Control 1 dup",
                sequence_order=2,
            )

    def test_same_step_key_different_occurrence_key_allowed(self, batch: Batch) -> None:
        BatchStep.objects.create(
            batch=batch,
            step_key="ctrl",
            occurrence_key="ctrl_per_box_1",
            title="Control 1",
            sequence_order=1,
        )
        step2 = BatchStep.objects.create(
            batch=batch,
            step_key="ctrl",
            occurrence_key="ctrl_per_box_2",
            title="Control 2",
            sequence_order=2,
        )
        assert step2.pk is not None

    def test_ordering_by_sequence_order(self, batch: Batch) -> None:
        BatchStep.objects.create(batch=batch, step_key="b", title="B", sequence_order=20)
        BatchStep.objects.create(batch=batch, step_key="a", title="A", sequence_order=10)
        steps = list(BatchStep.objects.filter(batch=batch))
        assert steps[0].step_key == "a"
        assert steps[1].step_key == "b"

    def test_cascade_delete_with_batch(self, batch: Batch) -> None:
        BatchStep.objects.create(
            batch=batch,
            step_key="x",
            title="X",
            sequence_order=1,
        )
        batch.delete()
        assert BatchStep.objects.count() == 0


@pytest.mark.django_db
class TestBatchDocumentRequirementModel:
    def test_create_doc_requirement_with_defaults(self, batch: Batch) -> None:
        doc = BatchDocumentRequirement.objects.create(
            batch=batch,
            document_code="fabrication_bulk",
            title="Fabrication bulk",
        )
        assert doc.is_required is True
        assert doc.is_applicable is True
        assert doc.repeat_mode == BatchDocumentRepeatMode.SINGLE
        assert doc.expected_count == 1
        assert doc.actual_count == 0
        assert doc.status == BatchDocumentStatus.EXPECTED

    def test_doc_requirement_str(self, batch: Batch) -> None:
        doc = BatchDocumentRequirement.objects.create(
            batch=batch,
            document_code="weighing",
            title="Weighing",
        )
        assert str(doc) == "LOT-2026-001 / weighing"

    def test_unique_constraint_batch_document_code(self, batch: Batch) -> None:
        BatchDocumentRequirement.objects.create(
            batch=batch,
            document_code="dup_code",
            title="Doc 1",
        )
        with pytest.raises(IntegrityError):
            BatchDocumentRequirement.objects.create(
                batch=batch,
                document_code="dup_code",
                title="Doc 2",
            )

    def test_cascade_delete_with_batch(self, batch: Batch) -> None:
        BatchDocumentRequirement.objects.create(
            batch=batch,
            document_code="doc1",
            title="Doc",
        )
        batch.delete()
        assert BatchDocumentRequirement.objects.count() == 0


@pytest.mark.django_db
class TestEnumValues:
    def test_batch_status_values(self) -> None:
        assert BatchStatus.DRAFT == "draft"
        assert BatchStatus.IN_EXECUTION == "in_execution"
        assert BatchStatus.RELEASED == "released"

    def test_batch_step_status_values(self) -> None:
        assert BatchStepStatus.NOT_STARTED == "not_started"
        assert BatchStepStatus.COMPLETED == "completed"
        assert BatchStepStatus.APPROVED == "approved"

    def test_repeat_mode_values(self) -> None:
        assert BatchDocumentRepeatMode.SINGLE == "single"
        assert BatchDocumentRepeatMode.PER_SHIFT == "per_shift"
        assert BatchDocumentRepeatMode.PER_TEAM == "per_team"
        assert BatchDocumentRepeatMode.PER_BOX == "per_box"
        assert BatchDocumentRepeatMode.PER_EVENT == "per_event"

    def test_step_review_state_values(self) -> None:
        assert StepReviewState.NONE == "none"
        assert StepReviewState.APPROVED == "approved"

    def test_step_signature_state_values(self) -> None:
        assert StepSignatureState.NOT_REQUIRED == "not_required"
        assert StepSignatureState.SIGNED == "signed"
