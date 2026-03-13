"""Domain unit tests for pre-QA review services."""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from apps.audit.models import AuditEvent, AuditEventType
from apps.authz.models import User
from apps.batches.models import Batch, BatchStatus, BatchStep, StepStatus
from apps.reviews.domain.pre_qa_review import confirm_pre_qa_review, mark_step_reviewed
from apps.reviews.models import ReviewEvent, ReviewEventType
from apps.sites.models import Site

_UserModel = get_user_model()


@pytest.fixture()
def site(db: None) -> Site:
    return Site.objects.create(code="factory-1", name="Factory 1")


@pytest.fixture()
def reviewer(db: None) -> User:
    return _UserModel.objects.create_user(username="reviewer", password="testpass1234")


@pytest.fixture()
def batch_awaiting_pre_qa(site: Site) -> Batch:
    return Batch.objects.create(
        reference="LOT-2026-0042",
        status=BatchStatus.AWAITING_PRE_QA,
        site=site,
    )


@pytest.fixture()
def batch_in_pre_qa_review(site: Site) -> Batch:
    return Batch.objects.create(
        reference="LOT-2026-0043",
        status=BatchStatus.IN_PRE_QA_REVIEW,
        site=site,
    )


@pytest.fixture()
def batch_in_progress(site: Site) -> Batch:
    return Batch.objects.create(
        reference="LOT-2026-0044",
        status=BatchStatus.IN_PROGRESS,
        site=site,
    )


# --- confirm_pre_qa_review tests ---


@pytest.mark.django_db()
class TestConfirmPreQaReview:
    def test_confirm_succeeds_from_awaiting_pre_qa_green(
        self,
        batch_awaiting_pre_qa: Batch,
        reviewer: User,
    ) -> None:
        # No steps → green severity
        result = confirm_pre_qa_review(batch=batch_awaiting_pre_qa, reviewer=reviewer)
        assert result.status == BatchStatus.AWAITING_QUALITY_REVIEW

    def test_confirm_succeeds_from_in_pre_qa_review(
        self,
        batch_in_pre_qa_review: Batch,
        reviewer: User,
    ) -> None:
        result = confirm_pre_qa_review(batch=batch_in_pre_qa_review, reviewer=reviewer)
        assert result.status == BatchStatus.AWAITING_QUALITY_REVIEW

    def test_confirm_succeeds_with_amber_severity(
        self,
        batch_awaiting_pre_qa: Batch,
        reviewer: User,
    ) -> None:
        # Step with non-blocking exception → amber severity
        BatchStep.objects.create(
            batch=batch_awaiting_pre_qa,
            order=1,
            reference="Step 1",
            status=StepStatus.COMPLETE,
            has_open_exception=True,
            open_exception_is_blocking=False,
        )
        result = confirm_pre_qa_review(batch=batch_awaiting_pre_qa, reviewer=reviewer)
        assert result.status == BatchStatus.AWAITING_QUALITY_REVIEW

    def test_confirm_fails_with_red_severity(
        self,
        batch_awaiting_pre_qa: Batch,
        reviewer: User,
    ) -> None:
        # Step with missing required data → red severity
        BatchStep.objects.create(
            batch=batch_awaiting_pre_qa,
            order=1,
            reference="Step 1",
            status=StepStatus.IN_PROGRESS,
            required_data_complete=False,
        )
        with pytest.raises(ValidationError, match="blocking issues remain"):
            confirm_pre_qa_review(batch=batch_awaiting_pre_qa, reviewer=reviewer)

    def test_confirm_fails_from_invalid_state(
        self,
        batch_in_progress: Batch,
        reviewer: User,
    ) -> None:
        with pytest.raises(ValidationError, match="awaiting_pre_qa or in_pre_qa_review"):
            confirm_pre_qa_review(batch=batch_in_progress, reviewer=reviewer)

    def test_confirm_fails_from_released_state(
        self,
        site: Site,
        reviewer: User,
    ) -> None:
        released_batch = Batch.objects.create(
            reference="LOT-RELEASED", status=BatchStatus.RELEASED, site=site
        )
        with pytest.raises(ValidationError, match="awaiting_pre_qa or in_pre_qa_review"):
            confirm_pre_qa_review(batch=released_batch, reviewer=reviewer)

    def test_confirm_creates_review_event(
        self,
        batch_awaiting_pre_qa: Batch,
        reviewer: User,
    ) -> None:
        confirm_pre_qa_review(
            batch=batch_awaiting_pre_qa, reviewer=reviewer, note="All good"
        )
        event = ReviewEvent.objects.get(batch=batch_awaiting_pre_qa)
        assert event.event_type == ReviewEventType.PRE_QA_CONFIRMED
        assert event.reviewer == reviewer
        assert event.note == "All good"
        assert event.step is None

    def test_confirm_records_audit_event(
        self,
        batch_awaiting_pre_qa: Batch,
        reviewer: User,
    ) -> None:
        confirm_pre_qa_review(batch=batch_awaiting_pre_qa, reviewer=reviewer)
        audit = AuditEvent.objects.filter(
            event_type=AuditEventType.PRE_QA_REVIEW_CONFIRMED
        ).first()
        assert audit is not None
        assert audit.actor == reviewer
        assert audit.site == batch_awaiting_pre_qa.site
        assert audit.metadata["batch_id"] == batch_awaiting_pre_qa.pk
        assert audit.metadata["batch_reference"] == batch_awaiting_pre_qa.reference


# --- mark_step_reviewed tests ---


@pytest.mark.django_db()
class TestMarkStepReviewed:
    def test_clears_changed_since_review_flag(
        self,
        batch_awaiting_pre_qa: Batch,
        reviewer: User,
    ) -> None:
        step = BatchStep.objects.create(
            batch=batch_awaiting_pre_qa,
            order=1,
            reference="Step 1",
            status=StepStatus.COMPLETE,
            changed_since_review=True,
        )
        updated = mark_step_reviewed(
            batch=batch_awaiting_pre_qa, step=step, reviewer=reviewer
        )
        assert updated.changed_since_review is False

    def test_clears_review_required_flag(
        self,
        batch_awaiting_pre_qa: Batch,
        reviewer: User,
    ) -> None:
        step = BatchStep.objects.create(
            batch=batch_awaiting_pre_qa,
            order=1,
            reference="Step 1",
            status=StepStatus.COMPLETE,
            review_required=True,
        )
        updated = mark_step_reviewed(
            batch=batch_awaiting_pre_qa, step=step, reviewer=reviewer
        )
        assert updated.review_required is False

    def test_transitions_batch_to_in_pre_qa_review(
        self,
        batch_awaiting_pre_qa: Batch,
        reviewer: User,
    ) -> None:
        step = BatchStep.objects.create(
            batch=batch_awaiting_pre_qa,
            order=1,
            reference="Step 1",
            status=StepStatus.COMPLETE,
            changed_since_review=True,
        )
        mark_step_reviewed(
            batch=batch_awaiting_pre_qa, step=step, reviewer=reviewer
        )
        batch_awaiting_pre_qa.refresh_from_db()
        assert batch_awaiting_pre_qa.status == BatchStatus.IN_PRE_QA_REVIEW

    def test_does_not_transition_if_already_in_pre_qa_review(
        self,
        batch_in_pre_qa_review: Batch,
        reviewer: User,
    ) -> None:
        step = BatchStep.objects.create(
            batch=batch_in_pre_qa_review,
            order=1,
            reference="Step 1",
            status=StepStatus.COMPLETE,
            changed_since_review=True,
        )
        mark_step_reviewed(
            batch=batch_in_pre_qa_review, step=step, reviewer=reviewer
        )
        batch_in_pre_qa_review.refresh_from_db()
        assert batch_in_pre_qa_review.status == BatchStatus.IN_PRE_QA_REVIEW

    def test_fails_for_step_without_reviewable_flags(
        self,
        batch_awaiting_pre_qa: Batch,
        reviewer: User,
    ) -> None:
        step = BatchStep.objects.create(
            batch=batch_awaiting_pre_qa,
            order=1,
            reference="Step 1",
            status=StepStatus.COMPLETE,
        )
        with pytest.raises(ValidationError, match="no reviewable flags"):
            mark_step_reviewed(
                batch=batch_awaiting_pre_qa, step=step, reviewer=reviewer
            )

    def test_fails_for_step_not_in_batch(
        self,
        batch_awaiting_pre_qa: Batch,
        site: Site,
        reviewer: User,
    ) -> None:
        other_batch = Batch.objects.create(
            reference="LOT-OTHER", status=BatchStatus.AWAITING_PRE_QA, site=site
        )
        step = BatchStep.objects.create(
            batch=other_batch,
            order=1,
            reference="Step 1",
            status=StepStatus.COMPLETE,
            changed_since_review=True,
        )
        with pytest.raises(ValidationError, match="does not belong"):
            mark_step_reviewed(
                batch=batch_awaiting_pre_qa, step=step, reviewer=reviewer
            )

    def test_fails_from_invalid_batch_state(
        self,
        batch_in_progress: Batch,
        reviewer: User,
    ) -> None:
        step = BatchStep.objects.create(
            batch=batch_in_progress,
            order=1,
            reference="Step 1",
            status=StepStatus.COMPLETE,
            changed_since_review=True,
        )
        with pytest.raises(ValidationError, match="awaiting_pre_qa or in_pre_qa_review"):
            mark_step_reviewed(
                batch=batch_in_progress, step=step, reviewer=reviewer
            )

    def test_creates_review_event(
        self,
        batch_awaiting_pre_qa: Batch,
        reviewer: User,
    ) -> None:
        step = BatchStep.objects.create(
            batch=batch_awaiting_pre_qa,
            order=1,
            reference="Step 1",
            status=StepStatus.COMPLETE,
            changed_since_review=True,
        )
        mark_step_reviewed(
            batch=batch_awaiting_pre_qa,
            step=step,
            reviewer=reviewer,
            note="Verified",
        )
        event = ReviewEvent.objects.get(batch=batch_awaiting_pre_qa)
        assert event.event_type == ReviewEventType.CHANGE_MARKED_REVIEWED
        assert event.step == step
        assert event.note == "Verified"

    def test_records_audit_event(
        self,
        batch_awaiting_pre_qa: Batch,
        reviewer: User,
    ) -> None:
        step = BatchStep.objects.create(
            batch=batch_awaiting_pre_qa,
            order=1,
            reference="Step 1",
            status=StepStatus.COMPLETE,
            changed_since_review=True,
        )
        mark_step_reviewed(
            batch=batch_awaiting_pre_qa, step=step, reviewer=reviewer
        )
        audit = AuditEvent.objects.filter(
            event_type=AuditEventType.REVIEW_ITEM_MARKED_REVIEWED
        ).first()
        assert audit is not None
        assert audit.metadata["step_id"] == step.pk
        assert audit.metadata["step_reference"] == "Step 1"

    def test_changed_since_signature_counts_as_reviewable(
        self,
        batch_awaiting_pre_qa: Batch,
        reviewer: User,
    ) -> None:
        step = BatchStep.objects.create(
            batch=batch_awaiting_pre_qa,
            order=1,
            reference="Step 1",
            status=StepStatus.COMPLETE,
            changed_since_signature=True,
        )
        # Should not raise — changed_since_signature is a reviewable flag
        updated = mark_step_reviewed(
            batch=batch_awaiting_pre_qa, step=step, reviewer=reviewer
        )
        # changed_since_signature is NOT cleared by mark_step_reviewed
        # (only changed_since_review and review_required are cleared)
        assert updated.changed_since_signature is True
