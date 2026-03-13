"""Tests for the review summary selector (DB queries + domain composition)."""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model

from apps.authz.models import User
from apps.batches.models import (
    Batch,
    BatchStatus,
    BatchStep,
    DossierChecklistItem,
    StepSignature,
    StepStatus,
)
from apps.reviews.selectors.review_summary import get_batch_review_summary
from apps.sites.models import Site

_UserModel = get_user_model()


@pytest.fixture()
def site(db: None) -> Site:
    return Site.objects.create(code="factory-1", name="Factory 1")


@pytest.fixture()
def batch_creator(db: None) -> User:
    return _UserModel.objects.create_user(username="creator", password="testpass1234")


@pytest.fixture()
def batch(site: Site, batch_creator: User) -> Batch:
    return Batch.objects.create(
        batch_number="LOT-2026-0001",
        status=BatchStatus.AWAITING_PRE_QA,
        site=site,
        snapshot_json={},
        created_by=batch_creator,
    )


@pytest.fixture()
def signer(db: None) -> User:
    return _UserModel.objects.create_user(username="signer", password="testpass1234")


def _step(batch: Batch, seq: int, **kwargs: object) -> BatchStep:
    """Helper to create a BatchStep with required fields."""
    defaults: dict[str, object] = {
        "step_key": f"step-{seq}",
        "title": kwargs.pop("title", f"Step {seq}"),
        "sequence_order": seq,
    }
    defaults.update(kwargs)
    return BatchStep.objects.create(batch=batch, **defaults)


@pytest.mark.django_db()
class TestGetBatchReviewSummary:
    def test_empty_batch_returns_green(self, batch: Batch) -> None:
        summary = get_batch_review_summary(batch)
        assert summary.batch_id == batch.pk
        assert summary.batch_number == "LOT-2026-0001"
        assert summary.batch_status == "awaiting_pre_qa"
        assert summary.severity == "green"
        assert summary.step_summary.total == 0
        assert summary.flagged_steps == ()
        assert summary.checklist.expected_documents == 0

    def test_batch_id_input_is_supported(self, batch: Batch) -> None:
        summary = get_batch_review_summary(batch.pk)
        assert summary.batch_id == batch.pk

    def test_all_steps_signed_returns_green(self, batch: Batch, signer: User) -> None:
        step1 = _step(
            batch,
            1,
            status=StepStatus.SIGNED,
            signature_state="required",
        )
        step2 = _step(
            batch,
            2,
            status=StepStatus.SIGNED,
            signature_state="required",
        )
        StepSignature.objects.create(step=step1, signer=signer, meaning="executed_by")
        StepSignature.objects.create(step=step2, signer=signer, meaning="executed_by")

        summary = get_batch_review_summary(batch)
        assert summary.severity == "green"
        assert summary.step_summary.signed == 2
        assert summary.flags.missing_required_signatures == 0

    def test_missing_signature_returns_red(self, batch: Batch) -> None:
        _step(
            batch,
            1,
            status=StepStatus.COMPLETE,
            signature_state="required",
        )
        summary = get_batch_review_summary(batch)
        assert summary.severity == "red"
        assert summary.flags.missing_required_signatures == 1
        assert len(summary.flagged_steps) == 1
        assert summary.flagged_steps[0].severity == "red"

    def test_missing_data_returns_red(self, batch: Batch) -> None:
        _step(
            batch,
            1,
            status=StepStatus.IN_PROGRESS,
            required_data_complete=False,
        )
        summary = get_batch_review_summary(batch)
        assert summary.severity == "red"
        assert summary.flags.missing_required_data == 1

    def test_changed_since_review_returns_amber(self, batch: Batch, signer: User) -> None:
        step = _step(
            batch,
            1,
            status=StepStatus.SIGNED,
            signature_state="required",
            changed_since_review=True,
        )
        StepSignature.objects.create(step=step, signer=signer, meaning="executed_by")

        summary = get_batch_review_summary(batch)
        assert summary.severity == "amber"
        assert summary.flags.changed_since_review == 1

    def test_checklist_with_missing_documents(self, batch: Batch) -> None:
        DossierChecklistItem.objects.create(
            batch=batch,
            document_name="weighing-record",
            is_present=True,
        )
        DossierChecklistItem.objects.create(
            batch=batch,
            document_name="mixing-record",
            is_present=False,
        )

        summary = get_batch_review_summary(batch)
        assert summary.checklist.expected_documents == 2
        assert summary.checklist.present_documents == 1
        assert summary.checklist.missing_documents == ("mixing-record",)

    def test_partial_completion(self, batch: Batch) -> None:
        _step(batch, 1, status=StepStatus.COMPLETE)
        _step(batch, 2, status=StepStatus.NOT_STARTED)
        _step(batch, 3, status=StepStatus.IN_PROGRESS)

        summary = get_batch_review_summary(batch)
        assert summary.step_summary.total == 3
        assert summary.step_summary.complete == 1
        assert summary.step_summary.not_started == 1
        assert summary.step_summary.in_progress == 1
        assert summary.severity == "amber"

    def test_blocking_open_exception_returns_red(self, batch: Batch) -> None:
        _step(
            batch,
            1,
            status=StepStatus.COMPLETE,
            has_open_exception=True,
            open_exception_is_blocking=True,
        )
        summary = get_batch_review_summary(batch)
        assert summary.severity == "red"
        assert summary.flags.open_exceptions == 1
        assert summary.flags.blocking_open_exceptions == 1

    def test_non_blocking_open_exception_returns_amber(self, batch: Batch) -> None:
        _step(
            batch,
            1,
            status=StepStatus.COMPLETE,
            has_open_exception=True,
            open_exception_is_blocking=False,
        )
        summary = get_batch_review_summary(batch)
        assert summary.severity == "amber"
        assert summary.flags.open_exceptions == 1
        assert summary.flags.blocking_open_exceptions == 0

    def test_flagged_steps_contain_correct_details(self, batch: Batch) -> None:
        _step(
            batch,
            1,
            title="Step 1 - Weighing",
            status=StepStatus.IN_PROGRESS,
            required_data_complete=False,
        )
        _step(
            batch,
            2,
            title="Step 2 - Mixing",
            status=StepStatus.COMPLETE,
            changed_since_review=True,
        )

        summary = get_batch_review_summary(batch)
        assert len(summary.flagged_steps) == 2

        step1 = next(s for s in summary.flagged_steps if s.step_reference == "Step 1 - Weighing")
        assert step1.severity == "red"
        assert "missing_required_data" in step1.flags

        step2 = next(s for s in summary.flagged_steps if s.step_reference == "Step 2 - Mixing")
        assert step2.severity == "amber"
        assert "changed_since_review" in step2.flags
