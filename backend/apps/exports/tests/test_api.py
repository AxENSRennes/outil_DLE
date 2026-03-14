"""API endpoint tests for the exports app."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.authz.models import SiteRole, SiteRoleAssignment
from apps.authz.tests.helpers import csrf_client, post_json
from apps.batches.models import Batch
from apps.exports.domain.composition import resolve_dossier_structure
from apps.exports.models import DossierProfile
from apps.mmr.models import MMR, MMRVersion
from apps.sites.models import Product, Site

User = get_user_model()


def _make_api_fixtures(
    *,
    with_profile: bool = True,
    with_structure: bool = False,
) -> dict[str, Any]:
    """Create minimal fixtures for API tests."""
    site = Site.objects.create(code=f"site-api-{Site.objects.count()}", name="API Test Site")
    product = Product.objects.create(
        site=site, name="Test Product", code=f"PROD-A{Product.objects.count()}"
    )
    user = User.objects.create_user(
        username=f"api-user-{User.objects.count()}", password="testpass"
    )
    SiteRoleAssignment.objects.create(user=user, site=site, role=SiteRole.OPERATOR)
    mmr = MMR.objects.create(
        site=site, product=product, name="API MMR", code=f"MMR-A{MMR.objects.count()}"
    )
    version = MMRVersion.objects.create(
        mmr=mmr, version_number=1, schema_json={"schemaVersion": "v1"}, created_by=user
    )
    batch = Batch.objects.create(
        site=site,
        mmr_version_id=version.pk,
        batch_number=f"BATCH-A{Batch.objects.count():04d}",
        batch_context_json={"paillette_present": True, "format_family": "CREAM"},
        snapshot_json={},
        created_by=user,
    )

    profile = None
    if with_profile:
        profile = DossierProfile.objects.create(
            mmr_version=version,
            name="API Test Profile",
            rules={
                "default_required": ["batch-header", "weighing-record"],
                "conditions": [
                    {
                        "context_key": "paillette_present",
                        "operator": "eq",
                        "value": True,
                        "include_elements": ["paillette-control"],
                        "exclude_elements": [],
                    },
                ],
            },
            elements=[
                {"identifier": "batch-header", "type": "sub_document", "title": "Header"},
                {"identifier": "weighing-record", "type": "sub_document", "title": "Weighing"},
                {
                    "identifier": "paillette-control",
                    "type": "in_process_control",
                    "title": "Paillette",
                },
            ],
        )

    if with_structure:
        resolve_dossier_structure(batch, actor=user, site=site)

    return {
        "site": site,
        "user": user,
        "mmr": mmr,
        "version": version,
        "batch": batch,
        "profile": profile,
    }


@pytest.mark.django_db
class TestGetDossierStructure:
    def test_returns_resolved_structure_with_elements(self) -> None:
        fx = _make_api_fixtures(with_structure=True)
        client = APIClient()
        client.force_login(fx["user"])

        response = client.get(f"/api/v1/batches/{fx['batch'].pk}/dossier-structure/")

        assert response.status_code == 200
        data = response.json()
        assert data["batch_id"] == fx["batch"].pk
        assert data["is_active"] is True
        assert len(data["elements"]) == 3

        identifiers = [el["element_identifier"] for el in data["elements"]]
        assert "batch-header" in identifiers
        assert "weighing-record" in identifiers
        assert "paillette-control" in identifiers

    def test_returns_404_when_no_structure(self) -> None:
        fx = _make_api_fixtures(with_structure=False)
        client = APIClient()
        client.force_login(fx["user"])

        response = client.get(f"/api/v1/batches/{fx['batch'].pk}/dossier-structure/")

        assert response.status_code == 404

    def test_returns_404_for_nonexistent_batch(self) -> None:
        fx = _make_api_fixtures()
        client = APIClient()
        client.force_login(fx["user"])

        response = client.get("/api/v1/batches/99999/dossier-structure/")

        assert response.status_code == 404

    def test_unauthenticated_request_rejected(self) -> None:
        fx = _make_api_fixtures(with_structure=True)
        client = APIClient()

        response = client.get(f"/api/v1/batches/{fx['batch'].pk}/dossier-structure/")

        assert response.status_code == 403

    def test_wrong_role_rejected(self) -> None:
        fx = _make_api_fixtures(with_structure=True)
        wrong_user = User.objects.create_user(username="wrong-role-get", password="testpass")
        SiteRoleAssignment.objects.create(
            user=wrong_user,
            site=fx["site"],
            role=SiteRole.INTERNAL_CONFIGURATOR,
        )
        client = APIClient()
        client.force_login(wrong_user)

        response = client.get(f"/api/v1/batches/{fx['batch'].pk}/dossier-structure/")

        assert response.status_code == 403


@pytest.mark.django_db
class TestResolveDossier:
    def test_creates_and_returns_structure(self) -> None:
        fx = _make_api_fixtures(with_profile=True, with_structure=False)
        client, token = csrf_client(user=fx["user"])

        response = post_json(
            client,
            f"/api/v1/batches/{fx['batch'].pk}/resolve-dossier/",
            {},
            csrf_token=token,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["batch_id"] == fx["batch"].pk
        assert data["is_active"] is True
        assert len(data["elements"]) >= 2

    def test_idempotent_returns_existing(self) -> None:
        fx = _make_api_fixtures(with_profile=True, with_structure=True)
        client, token = csrf_client(user=fx["user"])

        response = post_json(
            client,
            f"/api/v1/batches/{fx['batch'].pk}/resolve-dossier/",
            {},
            csrf_token=token,
        )

        assert response.status_code == 200
        # Should still be the same structure (idempotent)
        data = response.json()
        assert data["is_active"] is True

    def test_unauthenticated_request_rejected(self) -> None:
        fx = _make_api_fixtures(with_profile=True)
        client = APIClient(enforce_csrf_checks=True)
        client.get("/admin/login/")
        token = client.cookies["csrftoken"].value

        response = post_json(
            client,
            f"/api/v1/batches/{fx['batch'].pk}/resolve-dossier/",
            {},
            csrf_token=token,
        )

        assert response.status_code == 403

    def test_csrf_enforced_on_post(self) -> None:
        fx = _make_api_fixtures(with_profile=True)
        client = APIClient(enforce_csrf_checks=True)
        client.force_login(fx["user"])

        # POST without CSRF token
        response = client.post(
            f"/api/v1/batches/{fx['batch'].pk}/resolve-dossier/",
            {},
            format="json",
        )

        assert response.status_code == 403

    def test_nonexistent_batch_returns_404(self) -> None:
        fx = _make_api_fixtures(with_profile=True)
        client, token = csrf_client(user=fx["user"])

        response = post_json(
            client,
            "/api/v1/batches/99999/resolve-dossier/",
            {},
            csrf_token=token,
        )

        assert response.status_code == 404

    def test_no_profile_returns_422(self) -> None:
        fx = _make_api_fixtures(with_profile=False)
        client, token = csrf_client(user=fx["user"])

        response = post_json(
            client,
            f"/api/v1/batches/{fx['batch'].pk}/resolve-dossier/",
            {},
            csrf_token=token,
        )

        assert response.status_code == 422
        data = response.json()
        assert data["code"] == "composition_error"

    def test_invalid_profile_configuration_returns_422(self) -> None:
        fx = _make_api_fixtures(with_profile=True)
        fx["profile"].rules = {
            "default_required": ["batch-header", "missing-element"],
            "conditions": [],
        }
        fx["profile"].save(update_fields=["rules"])
        client, token = csrf_client(user=fx["user"])

        response = post_json(
            client,
            f"/api/v1/batches/{fx['batch'].pk}/resolve-dossier/",
            {},
            csrf_token=token,
        )

        assert response.status_code == 422
        data = response.json()
        assert data["code"] == "composition_error"
        assert "unknown elements" in data["detail"]

    def test_returns_409_on_concurrent_race(self) -> None:
        fx = _make_api_fixtures(with_profile=True, with_structure=False)
        client, token = csrf_client(user=fx["user"])

        with patch(
            "apps.exports.api.views.get_batch_dossier_structure",
            return_value=None,
        ):
            response = post_json(
                client,
                f"/api/v1/batches/{fx['batch'].pk}/resolve-dossier/",
                {},
                csrf_token=token,
            )

        assert response.status_code == 409
        data = response.json()
        assert data["code"] == "dossier_structure_race"

    def test_force_re_resolves_structure(self) -> None:
        fx = _make_api_fixtures(with_profile=True, with_structure=True)
        client, token = csrf_client(user=fx["user"])

        from apps.exports.models import BatchDossierStructure

        original = BatchDossierStructure.objects.get(batch=fx["batch"], is_active=True)

        response = post_json(
            client,
            f"/api/v1/batches/{fx['batch'].pk}/resolve-dossier/?force=true",
            {},
            csrf_token=token,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["batch_id"] == fx["batch"].pk
        assert data["is_active"] is True
        assert data["id"] != original.pk

        original.refresh_from_db()
        assert original.is_active is False

    def test_wrong_role_rejected(self) -> None:
        fx = _make_api_fixtures(with_profile=True)
        wrong_user = User.objects.create_user(username="wrong-role-post", password="testpass")
        SiteRoleAssignment.objects.create(
            user=wrong_user,
            site=fx["site"],
            role=SiteRole.INTERNAL_CONFIGURATOR,
        )
        client, token = csrf_client(user=wrong_user)

        response = post_json(
            client,
            f"/api/v1/batches/{fx['batch'].pk}/resolve-dossier/",
            {},
            csrf_token=token,
        )

        assert response.status_code == 403
