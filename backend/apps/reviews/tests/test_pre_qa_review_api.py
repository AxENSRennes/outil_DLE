"""API integration tests for pre-QA review endpoints."""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.authz.models import SiteRole, SiteRoleAssignment, User
from apps.batches.models import (
    Batch,
    BatchStatus,
    BatchStep,
    StepStatus,
)
from apps.mmr.models import MMR, MMRVersion
from apps.sites.models import Product, Site

_UserModel = get_user_model()


@pytest.fixture()
def site(db: None) -> Site:
    return Site.objects.create(code="factory-1", name="Factory 1")


@pytest.fixture()
def mmr_version(site: Site) -> MMRVersion:
    user = _UserModel.objects.create_user(username="template_author", password="testpass1234")
    product = Product.objects.create(site=site, name="Test Product", code="PROD-001")
    mmr = MMR.objects.create(site=site, product=product, name="Test MMR", code="MMR-001")
    return MMRVersion.objects.create(mmr=mmr, version_number=1, created_by=user)


@pytest.fixture()
def batch_creator() -> User:
    return _UserModel.objects.create_user(username="batch_creator", password="testpass1234")


@pytest.fixture()
def batch_awaiting_pre_qa(site: Site, mmr_version: MMRVersion, batch_creator: User) -> Batch:
    return Batch.objects.create(
        batch_number="LOT-2026-0042",
        status=BatchStatus.AWAITING_PRE_QA,
        site=site,
        mmr_version=mmr_version,
        created_by=batch_creator,
    )


@pytest.fixture()
def batch_in_pre_qa_review(site: Site, mmr_version: MMRVersion, batch_creator: User) -> Batch:
    return Batch.objects.create(
        batch_number="LOT-2026-0043",
        status=BatchStatus.IN_PRE_QA_REVIEW,
        site=site,
        mmr_version=mmr_version,
        created_by=batch_creator,
    )


@pytest.fixture()
def batch_in_progress(site: Site, mmr_version: MMRVersion, batch_creator: User) -> Batch:
    return Batch.objects.create(
        batch_number="LOT-2026-0044",
        status=BatchStatus.IN_PROGRESS,
        site=site,
        mmr_version=mmr_version,
        created_by=batch_creator,
    )


@pytest.fixture()
def production_reviewer(site: Site) -> User:
    user = _UserModel.objects.create_user(username="reviewer", password="testpass1234")
    SiteRoleAssignment.objects.create(
        user=user,
        site=site,
        role=SiteRole.PRODUCTION_REVIEWER,
    )
    return user


@pytest.fixture()
def quality_reviewer(site: Site) -> User:
    user = _UserModel.objects.create_user(username="qa_reviewer", password="testpass1234")
    SiteRoleAssignment.objects.create(
        user=user,
        site=site,
        role=SiteRole.QUALITY_REVIEWER,
    )
    return user


def _confirm_url(batch_id: int) -> str:
    return f"/api/v1/batches/{batch_id}/pre-qa-review/confirm"


def _mark_reviewed_url(batch_id: int, step_id: int) -> str:
    return f"/api/v1/batches/{batch_id}/review-items/{step_id}/mark-reviewed"


# --- Confirm Pre-QA Review endpoint tests ---


@pytest.mark.django_db()
class TestConfirmPreQaReviewAuth:
    def test_unauthenticated_returns_401(self, batch_awaiting_pre_qa: Batch) -> None:
        client = APIClient()
        response = client.post(
            _confirm_url(batch_awaiting_pre_qa.pk),
            data={},
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_quality_reviewer_returns_404(
        self,
        batch_awaiting_pre_qa: Batch,
        quality_reviewer: User,
    ) -> None:
        client = APIClient()
        client.force_authenticate(user=quality_reviewer)
        response = client.post(
            _confirm_url(batch_awaiting_pre_qa.pk),
            data={},
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_nonexistent_batch_returns_404(
        self,
        production_reviewer: User,
    ) -> None:
        client = APIClient()
        client.force_authenticate(user=production_reviewer)
        response = client.post(
            _confirm_url(99999),
            data={},
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db()
class TestConfirmPreQaReviewSuccess:
    def test_confirm_returns_200_and_correct_shape(
        self,
        batch_awaiting_pre_qa: Batch,
        production_reviewer: User,
    ) -> None:
        client = APIClient()
        client.force_authenticate(user=production_reviewer)
        response = client.post(
            _confirm_url(batch_awaiting_pre_qa.pk),
            data={"note": "All good"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["batch_id"] == batch_awaiting_pre_qa.pk
        assert data["batch_number"] == "LOT-2026-0042"
        assert data["batch_status"] == "awaiting_quality_review"
        assert data["confirmed_at"] is not None
        assert data["reviewer_note"] == "All good"

    def test_confirm_from_in_pre_qa_review(
        self,
        batch_in_pre_qa_review: Batch,
        production_reviewer: User,
    ) -> None:
        client = APIClient()
        client.force_authenticate(user=production_reviewer)
        response = client.post(
            _confirm_url(batch_in_pre_qa_review.pk),
            data={},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["batch_status"] == "awaiting_quality_review"

    def test_confirm_with_amber_severity_succeeds(
        self,
        batch_awaiting_pre_qa: Batch,
        production_reviewer: User,
    ) -> None:
        BatchStep.objects.create(
            batch=batch_awaiting_pre_qa,
            order=1,
            reference="Step 1",
            status=StepStatus.COMPLETE,
            has_open_exception=True,
            open_exception_is_blocking=False,
        )
        client = APIClient()
        client.force_authenticate(user=production_reviewer)
        response = client.post(
            _confirm_url(batch_awaiting_pre_qa.pk),
            data={},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db()
class TestConfirmPreQaReviewErrors:
    def test_confirm_blocked_with_red_severity_returns_400(
        self,
        batch_awaiting_pre_qa: Batch,
        production_reviewer: User,
    ) -> None:
        BatchStep.objects.create(
            batch=batch_awaiting_pre_qa,
            order=1,
            reference="Step 1",
            status=StepStatus.IN_PROGRESS,
            required_data_complete=False,
        )
        client = APIClient()
        client.force_authenticate(user=production_reviewer)
        response = client.post(
            _confirm_url(batch_awaiting_pre_qa.pk),
            data={},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_confirm_invalid_batch_state_returns_400(
        self,
        batch_in_progress: Batch,
        production_reviewer: User,
    ) -> None:
        client = APIClient()
        client.force_authenticate(user=production_reviewer)
        response = client.post(
            _confirm_url(batch_in_progress.pk),
            data={},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# --- Mark Step Reviewed endpoint tests ---


@pytest.mark.django_db()
class TestMarkStepReviewedAuth:
    def test_unauthenticated_returns_401(
        self,
        batch_awaiting_pre_qa: Batch,
    ) -> None:
        step = BatchStep.objects.create(
            batch=batch_awaiting_pre_qa,
            order=1,
            reference="Step 1",
            status=StepStatus.COMPLETE,
            changed_since_review=True,
        )
        client = APIClient()
        response = client.post(
            _mark_reviewed_url(batch_awaiting_pre_qa.pk, step.pk),
            data={},
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_quality_reviewer_returns_404(
        self,
        batch_awaiting_pre_qa: Batch,
        quality_reviewer: User,
    ) -> None:
        step = BatchStep.objects.create(
            batch=batch_awaiting_pre_qa,
            order=1,
            reference="Step 1",
            status=StepStatus.COMPLETE,
            changed_since_review=True,
        )
        client = APIClient()
        client.force_authenticate(user=quality_reviewer)
        response = client.post(
            _mark_reviewed_url(batch_awaiting_pre_qa.pk, step.pk),
            data={},
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db()
class TestMarkStepReviewedSuccess:
    def test_mark_reviewed_returns_200_and_correct_shape(
        self,
        batch_awaiting_pre_qa: Batch,
        production_reviewer: User,
    ) -> None:
        step = BatchStep.objects.create(
            batch=batch_awaiting_pre_qa,
            order=1,
            reference="Step 1 - Mixing",
            status=StepStatus.COMPLETE,
            changed_since_review=True,
            review_required=True,
        )
        client = APIClient()
        client.force_authenticate(user=production_reviewer)
        response = client.post(
            _mark_reviewed_url(batch_awaiting_pre_qa.pk, step.pk),
            data={"note": "Checked"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["step_id"] == step.pk
        assert data["step_reference"] == "Step 1 - Mixing"
        assert data["review_status"] == "reviewed"
        assert "changed_since_review" in data["flags_cleared"]
        assert "review_required" in data["flags_cleared"]
        assert data["batch_status"] == "in_pre_qa_review"


@pytest.mark.django_db()
class TestMarkStepReviewedErrors:
    def test_step_without_reviewable_flags_returns_400(
        self,
        batch_awaiting_pre_qa: Batch,
        production_reviewer: User,
    ) -> None:
        step = BatchStep.objects.create(
            batch=batch_awaiting_pre_qa,
            order=1,
            reference="Step 1",
            status=StepStatus.COMPLETE,
        )
        client = APIClient()
        client.force_authenticate(user=production_reviewer)
        response = client.post(
            _mark_reviewed_url(batch_awaiting_pre_qa.pk, step.pk),
            data={},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_step_not_in_batch_returns_404(
        self,
        batch_awaiting_pre_qa: Batch,
        site: Site,
        mmr_version: MMRVersion,
        batch_creator: User,
        production_reviewer: User,
    ) -> None:
        other_batch = Batch.objects.create(
            batch_number="LOT-OTHER",
            status=BatchStatus.AWAITING_PRE_QA,
            site=site,
            mmr_version=mmr_version,
            created_by=batch_creator,
        )
        step = BatchStep.objects.create(
            batch=other_batch,
            order=1,
            reference="Step 1",
            status=StepStatus.COMPLETE,
            changed_since_review=True,
        )
        client = APIClient()
        client.force_authenticate(user=production_reviewer)
        response = client.post(
            _mark_reviewed_url(batch_awaiting_pre_qa.pk, step.pk),
            data={},
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_nonexistent_step_returns_404(
        self,
        batch_awaiting_pre_qa: Batch,
        production_reviewer: User,
    ) -> None:
        client = APIClient()
        client.force_authenticate(user=production_reviewer)
        response = client.post(
            _mark_reviewed_url(batch_awaiting_pre_qa.pk, 99999),
            data={},
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
