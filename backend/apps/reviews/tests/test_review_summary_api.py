"""API integration tests for the review-summary endpoint."""

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
    DossierChecklistItem,
    StepSignature,
    StepStatus,
)
from apps.mmr.models import MMR, MMRVersion
from apps.sites.models import Product, Site

_UserModel = get_user_model()


@pytest.fixture()
def site(db: None) -> Site:
    return Site.objects.create(code="factory-1", name="Factory 1")


@pytest.fixture()
def other_site(db: None) -> Site:
    return Site.objects.create(code="factory-2", name="Factory 2")


@pytest.fixture()
def mmr_version(site: Site) -> MMRVersion:
    user = _UserModel.objects.create_user(username="template_author", password="testpass1234")
    product = Product.objects.create(site=site, name="Test Product", code="PROD-001")
    mmr = MMR.objects.create(site=site, product=product, name="Test MMR", code="MMR-001")
    return MMRVersion.objects.create(mmr=mmr, version_number=1, created_by=user)


@pytest.fixture()
def batch(site: Site, mmr_version: MMRVersion) -> Batch:
    user = _UserModel.objects.create_user(username="batch_creator", password="testpass1234")
    return Batch.objects.create(
        batch_number="LOT-2026-0042",
        status=BatchStatus.AWAITING_PRE_QA,
        site=site,
        mmr_version=mmr_version,
        created_by=user,
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


@pytest.fixture()
def operator(site: Site) -> User:
    user = _UserModel.objects.create_user(username="operator", password="testpass1234")
    SiteRoleAssignment.objects.create(
        user=user,
        site=site,
        role=SiteRole.OPERATOR,
    )
    return user


@pytest.fixture()
def wrong_site_reviewer(other_site: Site) -> User:
    user = _UserModel.objects.create_user(username="wrong_site_rev", password="testpass1234")
    SiteRoleAssignment.objects.create(
        user=user,
        site=other_site,
        role=SiteRole.PRODUCTION_REVIEWER,
    )
    return user


def _url(batch_id: int) -> str:
    return f"/api/v1/batches/{batch_id}/review-summary/"


@pytest.mark.django_db()
class TestReviewSummaryEndpointAuth:
    def test_unauthenticated_returns_401(self, batch: Batch) -> None:
        client = APIClient()
        response = client.get(_url(batch.pk))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_operator_returns_404(self, batch: Batch, operator: User) -> None:
        client = APIClient()
        client.force_authenticate(user=operator)
        response = client.get(_url(batch.pk))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_wrong_site_reviewer_returns_404(
        self,
        batch: Batch,
        wrong_site_reviewer: User,
    ) -> None:
        client = APIClient()
        client.force_authenticate(user=wrong_site_reviewer)
        response = client.get(_url(batch.pk))
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db()
class TestReviewSummaryEndpointSuccess:
    def test_production_reviewer_gets_200(
        self,
        batch: Batch,
        production_reviewer: User,
    ) -> None:
        client = APIClient()
        client.force_authenticate(user=production_reviewer)
        response = client.get(_url(batch.pk))
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["batch_id"] == batch.pk
        assert data["batch_number"] == "LOT-2026-0042"
        assert data["batch_status"] == "awaiting_pre_qa"
        assert data["severity"] == "green"

    def test_quality_reviewer_gets_200(
        self,
        batch: Batch,
        quality_reviewer: User,
    ) -> None:
        client = APIClient()
        client.force_authenticate(user=quality_reviewer)
        response = client.get(_url(batch.pk))
        assert response.status_code == status.HTTP_200_OK

    def test_batch_not_found_returns_404(self, production_reviewer: User) -> None:
        client = APIClient()
        client.force_authenticate(user=production_reviewer)
        response = client.get(_url(99999))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_response_shape(
        self,
        batch: Batch,
        production_reviewer: User,
    ) -> None:
        signer = _UserModel.objects.create_user(username="signer", password="testpass1234")
        step1 = BatchStep.objects.create(
            batch=batch,
            order=1,
            reference="Step 1 - Mixing",
            status=StepStatus.SIGNED,
            requires_signature=True,
        )
        StepSignature.objects.create(step=step1, signer=signer, meaning="executed_by")
        BatchStep.objects.create(
            batch=batch,
            order=2,
            reference="Step 2 - Weighing",
            status=StepStatus.IN_PROGRESS,
            required_data_complete=False,
        )
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

        client = APIClient()
        client.force_authenticate(user=production_reviewer)
        response = client.get(_url(batch.pk))
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify top-level fields
        assert data["severity"] == "red"

        # Verify step_summary
        ss = data["step_summary"]
        assert ss["total"] == 2
        assert ss["signed"] == 1
        assert ss["in_progress"] == 1

        # Verify flags
        fl = data["flags"]
        assert fl["missing_required_data"] == 1
        assert fl["missing_required_signatures"] == 0

        # Verify checklist
        cl = data["checklist"]
        assert cl["expected_documents"] == 2
        assert cl["present_documents"] == 1
        assert cl["missing_documents"] == ["mixing-record"]

        # Verify flagged_steps
        assert len(data["flagged_steps"]) == 1
        flagged = data["flagged_steps"][0]
        assert flagged["step_reference"] == "Step 2 - Weighing"
        assert flagged["severity"] == "red"
        assert "missing_required_data" in flagged["flags"]

    def test_all_signed_returns_green(
        self,
        batch: Batch,
        production_reviewer: User,
    ) -> None:
        signer = _UserModel.objects.create_user(username="signer2", password="testpass1234")
        for i in range(3):
            step = BatchStep.objects.create(
                batch=batch,
                order=i + 1,
                reference=f"Step {i + 1}",
                status=StepStatus.SIGNED,
                requires_signature=True,
            )
            StepSignature.objects.create(step=step, signer=signer, meaning="executed_by")

        client = APIClient()
        client.force_authenticate(user=production_reviewer)
        response = client.get(_url(batch.pk))
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["severity"] == "green"

    def test_batch_with_corrections_returns_amber(
        self,
        batch: Batch,
        production_reviewer: User,
    ) -> None:
        signer = _UserModel.objects.create_user(username="signer3", password="testpass1234")
        step = BatchStep.objects.create(
            batch=batch,
            order=1,
            reference="Step 1",
            status=StepStatus.SIGNED,
            requires_signature=True,
            changed_since_review=True,
        )
        StepSignature.objects.create(step=step, signer=signer, meaning="executed_by")

        client = APIClient()
        client.force_authenticate(user=production_reviewer)
        response = client.get(_url(batch.pk))
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["severity"] == "amber"

    def test_non_blocking_exception_returns_amber(
        self,
        batch: Batch,
        production_reviewer: User,
    ) -> None:
        BatchStep.objects.create(
            batch=batch,
            order=1,
            reference="Step 1",
            status=StepStatus.COMPLETE,
            has_open_exception=True,
            open_exception_is_blocking=False,
        )

        client = APIClient()
        client.force_authenticate(user=production_reviewer)
        response = client.get(_url(batch.pk))
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["severity"] == "amber"
