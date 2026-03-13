from __future__ import annotations

from typing import Any

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.authz.models import SiteRoleAssignment
from apps.authz.tests.helpers import csrf_client, post_json
from apps.batches.domain.composition import generate_repeated_controls
from apps.batches.models import Batch, BatchStep, BatchStepStatus

User = get_user_model()


@pytest.fixture()
def authed_client(user: Any) -> tuple[APIClient, str]:
    return csrf_client(user=user)


@pytest.mark.django_db
class TestComposeEndpoint:
    def test_compose_returns_step_count(
        self,
        authed_client: tuple[APIClient, str],
        batch_pms_glitter: Batch,
        operator_role: SiteRoleAssignment,
    ) -> None:
        client, token = authed_client
        response = post_json(
            client,
            f"/api/v1/batches/{batch_pms_glitter.pk}/compose",
            {},
            csrf_token=token,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["batch_id"] == batch_pms_glitter.pk
        assert data["steps_created"] == 11
        assert data["document_requirements_created"] == 9

    def test_compose_idempotent(
        self,
        authed_client: tuple[APIClient, str],
        batch_pms_glitter: Batch,
        operator_role: SiteRoleAssignment,
    ) -> None:
        client, token = authed_client
        post_json(
            client,
            f"/api/v1/batches/{batch_pms_glitter.pk}/compose",
            {},
            csrf_token=token,
        )
        response = post_json(
            client,
            f"/api/v1/batches/{batch_pms_glitter.pk}/compose",
            {},
            csrf_token=token,
        )
        assert response.status_code == 200
        assert BatchStep.objects.filter(batch=batch_pms_glitter).count() == 11

    def test_compose_preserves_in_progress(
        self,
        authed_client: tuple[APIClient, str],
        batch_pms_glitter: Batch,
        operator_role: SiteRoleAssignment,
    ) -> None:
        client, token = authed_client
        post_json(
            client,
            f"/api/v1/batches/{batch_pms_glitter.pk}/compose",
            {},
            csrf_token=token,
        )
        fab = BatchStep.objects.get(
            batch=batch_pms_glitter, step_key="fabrication_bulk"
        )
        fab.status = BatchStepStatus.IN_PROGRESS
        fab.data_json = {"saved": True}
        fab.save()

        # Re-compose
        post_json(
            client,
            f"/api/v1/batches/{batch_pms_glitter.pk}/compose",
            {},
            csrf_token=token,
        )
        fab.refresh_from_db()
        assert fab.status == BatchStepStatus.IN_PROGRESS
        assert fab.data_json == {"saved": True}

    def test_compose_404_for_nonexistent_batch(
        self,
        authed_client: tuple[APIClient, str],
        operator_role: SiteRoleAssignment,
    ) -> None:
        client, token = authed_client
        response = post_json(
            client, "/api/v1/batches/99999/compose", {}, csrf_token=token
        )
        assert response.status_code == 404

    def test_compose_requires_auth(self, batch_pms_glitter: Batch) -> None:
        client = APIClient()
        response = client.post(
            f"/api/v1/batches/{batch_pms_glitter.pk}/compose"
        )
        assert response.status_code == 403

    def test_compose_without_site_role_returns_403(
        self,
        authed_client: tuple[APIClient, str],
        batch_pms_glitter: Batch,
    ) -> None:
        client, token = authed_client
        response = post_json(
            client,
            f"/api/v1/batches/{batch_pms_glitter.pk}/compose",
            {},
            csrf_token=token,
        )
        assert response.status_code == 403


@pytest.mark.django_db
class TestAddOccurrenceEndpoint:
    def test_add_occurrence_returns_new_step(
        self,
        authed_client: tuple[APIClient, str],
        batch_pms_glitter: Batch,
        operator_role: SiteRoleAssignment,
    ) -> None:
        generate_repeated_controls(batch_pms_glitter)
        client, token = authed_client
        response = post_json(
            client,
            f"/api/v1/batches/{batch_pms_glitter.pk}/steps/finished_product_control/occurrences",
            {},
            csrf_token=token,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["step_key"] == "finished_product_control"
        assert data["occurrence_index"] == 2

    def test_add_occurrence_single_mode_returns_400(
        self,
        authed_client: tuple[APIClient, str],
        batch_pms_glitter: Batch,
        operator_role: SiteRoleAssignment,
    ) -> None:
        generate_repeated_controls(batch_pms_glitter)
        client, token = authed_client
        response = post_json(
            client,
            f"/api/v1/batches/{batch_pms_glitter.pk}/steps/fabrication_bulk/occurrences",
            {},
            csrf_token=token,
        )
        assert response.status_code == 400
        assert "single" in response.json()["detail"]

    def test_add_occurrence_without_site_role_returns_403(
        self,
        authed_client: tuple[APIClient, str],
        batch_pms_glitter: Batch,
    ) -> None:
        generate_repeated_controls(batch_pms_glitter)
        client, token = authed_client
        response = post_json(
            client,
            f"/api/v1/batches/{batch_pms_glitter.pk}/steps/finished_product_control/occurrences",
            {},
            csrf_token=token,
        )
        assert response.status_code == 403


@pytest.mark.django_db
class TestStepsListEndpoint:
    def test_returns_grouped_steps(
        self,
        authed_client: tuple[APIClient, str],
        batch_pms_glitter: Batch,
        operator_role: SiteRoleAssignment,
    ) -> None:
        generate_repeated_controls(batch_pms_glitter)
        client, _ = authed_client
        response = client.get(
            f"/api/v1/batches/{batch_pms_glitter.pk}/steps"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 9  # 9 step groups
        fpc = next(g for g in data if g["step_key"] == "finished_product_control")
        assert fpc["repeat_mode"] == "per_box"
        assert len(fpc["occurrences"]) == 1

    def test_gencod_has_3_occurrences(
        self,
        authed_client: tuple[APIClient, str],
        batch_pms_glitter: Batch,
        operator_role: SiteRoleAssignment,
    ) -> None:
        generate_repeated_controls(batch_pms_glitter)
        client, _ = authed_client
        response = client.get(
            f"/api/v1/batches/{batch_pms_glitter.pk}/steps"
        )
        data = response.json()
        gencod = next(
            g for g in data if g["step_key"] == "gencod_control_uni2_uni3"
        )
        assert len(gencod["occurrences"]) == 3

    def test_steps_list_without_site_role_returns_403(
        self,
        authed_client: tuple[APIClient, str],
        batch_pms_glitter: Batch,
    ) -> None:
        client, _ = authed_client
        response = client.get(
            f"/api/v1/batches/{batch_pms_glitter.pk}/steps"
        )
        assert response.status_code == 403


@pytest.mark.django_db
class TestDocumentRequirementsEndpoint:
    def test_returns_all_doc_requirements(
        self,
        authed_client: tuple[APIClient, str],
        batch_pms_glitter: Batch,
        operator_role: SiteRoleAssignment,
    ) -> None:
        generate_repeated_controls(batch_pms_glitter)
        client, _ = authed_client
        response = client.get(
            f"/api/v1/batches/{batch_pms_glitter.pk}/document-requirements"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 9

    def test_doc_requirement_shape(
        self,
        authed_client: tuple[APIClient, str],
        batch_pms_glitter: Batch,
        operator_role: SiteRoleAssignment,
    ) -> None:
        generate_repeated_controls(batch_pms_glitter)
        client, _ = authed_client
        response = client.get(
            f"/api/v1/batches/{batch_pms_glitter.pk}/document-requirements"
        )
        data = response.json()
        first = data[0]
        assert "document_code" in first
        assert "title" in first
        assert "repeat_mode" in first
        assert "expected_count" in first
        assert "actual_count" in first
        assert "is_applicable" in first

    def test_doc_requirements_without_site_role_returns_403(
        self,
        authed_client: tuple[APIClient, str],
        batch_pms_glitter: Batch,
    ) -> None:
        client, _ = authed_client
        response = client.get(
            f"/api/v1/batches/{batch_pms_glitter.pk}/document-requirements"
        )
        assert response.status_code == 403
