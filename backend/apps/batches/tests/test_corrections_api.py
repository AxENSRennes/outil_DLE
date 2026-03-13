from __future__ import annotations

from typing import Any

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.audit.models import AuditEvent, AuditEventType
from apps.authz.models import SiteRole, SiteRoleAssignment
from apps.authz.tests.helpers import csrf_client, post_json
from apps.batches.models import Batch, BatchStatus, BatchStep, StepStatus
from apps.sites.models import Site

_UserModel = get_user_model()


def _url(step_id: int) -> str:
    return f"/api/v1/batch-steps/{step_id}/corrections/"


@pytest.fixture()
def site(db: None) -> Site:
    return Site.objects.create(code="factory-1", name="Factory 1")


@pytest.fixture()
def batch(site: Site) -> Batch:
    return Batch.objects.create(
        reference="LOT-2026-0042",
        status=BatchStatus.IN_PROGRESS,
        site=site,
    )


@pytest.fixture()
def step(batch: Batch) -> BatchStep:
    return BatchStep.objects.create(
        batch=batch,
        order=1,
        reference="Step 1 - Mixing",
        status=StepStatus.IN_PROGRESS,
        data_json={"temperature": "22.5", "pressure": "1.013"},
    )


@pytest.fixture()
def operator(site: Site) -> Any:
    user = _UserModel.objects.create_user(username="operator", password="test-pass-123")
    SiteRoleAssignment.objects.create(user=user, site=site, role=SiteRole.OPERATOR)
    return user


@pytest.fixture()
def production_reviewer(site: Site) -> Any:
    user = _UserModel.objects.create_user(username="prod-reviewer", password="test-pass-123")
    SiteRoleAssignment.objects.create(user=user, site=site, role=SiteRole.PRODUCTION_REVIEWER)
    return user


@pytest.fixture()
def unauthorized_user(db: None) -> Any:
    return _UserModel.objects.create_user(username="unauthorized", password="test-pass-123")


def _valid_payload() -> dict[str, Any]:
    return {
        "corrections": [
            {"field_name": "temperature", "new_value": "23.1"},
        ],
        "reason_for_change": "Transcription error",
    }


@pytest.mark.django_db()
class TestSubmitCorrectionAuth:
    def test_unauthenticated_returns_401(self, batch: Batch, step: BatchStep) -> None:
        client = APIClient()
        resp = client.post(_url(step.pk), _valid_payload(), format="json")
        assert resp.status_code == 401

    def test_user_without_site_role_returns_404(
        self, batch: Batch, step: BatchStep, unauthorized_user: Any
    ) -> None:
        client, token = csrf_client(user=unauthorized_user)
        resp = post_json(client, _url(step.pk), _valid_payload(), csrf_token=token)
        assert resp.status_code == 404

    def test_operator_on_different_site_returns_404(self, batch: Batch, step: BatchStep) -> None:
        other_site = Site.objects.create(code="other-site", name="Other Site")
        user = _UserModel.objects.create_user(username="other-op", password="test-pass-123")
        SiteRoleAssignment.objects.create(user=user, site=other_site, role=SiteRole.OPERATOR)
        client, token = csrf_client(user=user)
        resp = post_json(client, _url(step.pk), _valid_payload(), csrf_token=token)
        assert resp.status_code == 404


@pytest.mark.django_db()
class TestSubmitCorrectionSuccess:
    def test_operator_can_submit_correction_201(
        self, batch: Batch, step: BatchStep, operator: Any
    ) -> None:
        client, token = csrf_client(user=operator)
        resp = post_json(client, _url(step.pk), _valid_payload(), csrf_token=token)

        assert resp.status_code == 201
        data = resp.json()
        assert "correction_id" in data
        assert data["step_id"] == step.pk
        assert "corrected_at" in data
        assert data["corrected_by"] == operator.pk
        assert len(data["corrections_applied"]) == 1
        assert data["corrections_applied"][0]["field_name"] == "temperature"
        assert data["corrections_applied"][0]["old_value"] == "22.5"
        assert data["corrections_applied"][0]["new_value"] == "23.1"
        assert data["reason_for_change"] == "Transcription error"

    def test_production_reviewer_can_submit_correction_201(
        self, batch: Batch, step: BatchStep, production_reviewer: Any
    ) -> None:
        client, token = csrf_client(user=production_reviewer)
        resp = post_json(client, _url(step.pk), _valid_payload(), csrf_token=token)
        assert resp.status_code == 201

    def test_audit_event_created_with_correct_metadata(
        self, batch: Batch, step: BatchStep, operator: Any
    ) -> None:
        client, token = csrf_client(user=operator)
        resp = post_json(client, _url(step.pk), _valid_payload(), csrf_token=token)

        assert resp.status_code == 201
        event = AuditEvent.objects.get(pk=resp.json()["correction_id"])
        assert event.event_type == AuditEventType.CORRECTION_SUBMITTED
        assert event.target_type == "batch_step"
        assert event.target_id == step.pk
        assert event.actor == operator
        assert event.metadata["batch_id"] == batch.pk
        assert event.metadata["reason_for_change"] == "Transcription error"
        assert len(event.metadata["corrections"]) == 1

    def test_step_data_updated_after_correction(
        self, batch: Batch, step: BatchStep, operator: Any
    ) -> None:
        client, token = csrf_client(user=operator)
        post_json(client, _url(step.pk), _valid_payload(), csrf_token=token)

        step.refresh_from_db()
        assert step.data_json["temperature"] == "23.1"

    def test_null_new_value_accepted(self, batch: Batch, step: BatchStep, operator: Any) -> None:
        client, token = csrf_client(user=operator)
        payload = {
            "corrections": [{"field_name": "temperature", "new_value": None}],
            "reason_for_change": "Clearing erroneous value",
        }
        resp = post_json(client, _url(step.pk), payload, csrf_token=token)

        assert resp.status_code == 201
        data = resp.json()
        assert data["corrections_applied"][0]["new_value"] is None
        step.refresh_from_db()
        assert step.data_json["temperature"] is None


@pytest.mark.django_db()
class TestSubmitCorrectionValidation:
    def test_missing_reason_for_change_returns_400(
        self, batch: Batch, step: BatchStep, operator: Any
    ) -> None:
        client, token = csrf_client(user=operator)
        payload = {
            "corrections": [{"field_name": "temperature", "new_value": "23.1"}],
        }
        resp = post_json(client, _url(step.pk), payload, csrf_token=token)
        assert resp.status_code == 400

    def test_empty_corrections_list_returns_400(
        self, batch: Batch, step: BatchStep, operator: Any
    ) -> None:
        client, token = csrf_client(user=operator)
        payload = {"corrections": [], "reason_for_change": "Fix"}
        resp = post_json(client, _url(step.pk), payload, csrf_token=token)
        assert resp.status_code == 400

    def test_non_existent_step_returns_404(self, batch: Batch, operator: Any) -> None:
        client, token = csrf_client(user=operator)
        resp = post_json(client, _url(99999), _valid_payload(), csrf_token=token)
        assert resp.status_code == 404

    def test_not_started_step_returns_400(self, batch: Batch, operator: Any) -> None:
        not_started_step = BatchStep.objects.create(
            batch=batch,
            order=2,
            reference="Step 2",
            status=StepStatus.NOT_STARTED,
        )
        client, token = csrf_client(user=operator)
        resp = post_json(client, _url(not_started_step.pk), _valid_payload(), csrf_token=token)
        assert resp.status_code == 400

    def test_duplicate_field_name_returns_400(
        self, batch: Batch, step: BatchStep, operator: Any
    ) -> None:
        client, token = csrf_client(user=operator)
        payload = {
            "corrections": [
                {"field_name": "temperature", "new_value": "23.1"},
                {"field_name": "temperature", "new_value": "24.0"},
            ],
            "reason_for_change": "Fix",
        }
        resp = post_json(client, _url(step.pk), payload, csrf_token=token)
        assert resp.status_code == 400

    def test_missing_new_value_returns_400(
        self, batch: Batch, step: BatchStep, operator: Any
    ) -> None:
        client, token = csrf_client(user=operator)
        payload = {
            "corrections": [{"field_name": "temperature"}],
            "reason_for_change": "Fix",
        }
        resp = post_json(client, _url(step.pk), payload, csrf_token=token)
        assert resp.status_code == 400

    def test_object_new_value_returns_400(
        self, batch: Batch, step: BatchStep, operator: Any
    ) -> None:
        client, token = csrf_client(user=operator)
        payload = {
            "corrections": [{"field_name": "temperature", "new_value": {"value": "23.1"}}],
            "reason_for_change": "Fix",
        }
        resp = post_json(client, _url(step.pk), payload, csrf_token=token)
        assert resp.status_code == 400

    def test_array_new_value_returns_400(
        self, batch: Batch, step: BatchStep, operator: Any
    ) -> None:
        client, token = csrf_client(user=operator)
        payload = {
            "corrections": [{"field_name": "temperature", "new_value": ["23.1"]}],
            "reason_for_change": "Fix",
        }
        resp = post_json(client, _url(step.pk), payload, csrf_token=token)
        assert resp.status_code == 400


@pytest.mark.django_db()
class TestSubmitCorrectionResponseShape:
    def test_response_has_all_required_fields(
        self, batch: Batch, step: BatchStep, operator: Any
    ) -> None:
        client, token = csrf_client(user=operator)
        payload = {
            "corrections": [
                {"field_name": "temperature", "new_value": "23.1"},
                {"field_name": "pressure", "new_value": "1.015"},
            ],
            "reason_for_change": "Transcription error on both readings",
        }
        resp = post_json(client, _url(step.pk), payload, csrf_token=token)

        assert resp.status_code == 201
        data = resp.json()
        assert set(data.keys()) == {
            "correction_id",
            "step_id",
            "corrected_at",
            "corrected_by",
            "corrections_applied",
            "reason_for_change",
        }
        assert len(data["corrections_applied"]) == 2
        for entry in data["corrections_applied"]:
            assert set(entry.keys()) == {"field_name", "old_value", "new_value"}
